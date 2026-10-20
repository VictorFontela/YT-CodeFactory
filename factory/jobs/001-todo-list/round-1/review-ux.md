VERDICT: PASS
COMMIT: 784f2329911b207275f3ebcd4a35951c1d688aa7

# Revisão de UX — rodada 1

Nenhuma correção obrigatória encontrada. O fluxo principal é imediato, a interface
está em português e os estados vazio, inválido, concluído e de falha de persistência
orientam a pessoa sem impedir o uso da lista.

## Evidência e verificação

- Li contrato, board, spec, build, README e diff de `main` até o commit registrado.
  `git rev-parse HEAD` confirmou exatamente o SHA acima. Não foi encontrado
  `AGENTS.md` aplicável. Não alterei código nem li outros pareceres desta rodada.
- Iniciei os servidores Python locais documentados e executei nesta revisão
  `node /tmp/todo-browser-check.cjs`, após ler seu conteúdo. O script existente de
  QA utiliza Chromium real com Playwright e terminou com exit 0. Os resultados
  abaixo foram reproduzidos nesta execução, não apenas extraídos do build.
- **CA1–CA2:** abertura da página, título e idioma; envio pelo botão e Enter,
  remoção de espaços externos, uma inserção por envio e campo novamente focado.
  Envios vazio e com espaços não criaram tarefas e mostraram orientação legível.
- **CA3–CA4:** tarefas com textos iguais permaneceram independentes ao concluir,
  reabrir e excluir. A conclusão apresenta caixa marcada e texto riscado. Excluir
  o último item recuperou a orientação para criar uma tarefa.
- **CA5:** recarga preservou textos, conclusão e exclusão. JSON inválido,
  estrutura incorreta e IDs duplicados geraram aviso e permitiram criar uma nova
  lista. Falha simulada de escrita e bloqueio total de `localStorage` mantiveram
  criação, conclusão e exclusão disponíveis, com aviso de possível perda.
- **CA6:** a árvore acessível expõe campo com rótulo, checkbox com texto da tarefa
  e botão com nome `Excluir tarefa: <texto>`. Exercitei Tab, Shift+Tab, Enter e
  Espaço por automação. A ordem é lógica, o foco de teclado tem outline visível
  e a exclusão focada moveu o foco à próxima tarefa ou ao campo quando a lista
  ficou vazia. Inspecionei também o destino à tarefa anterior no código.
- **CA7:** inspecionei visualmente as capturas desta execução em
  `/tmp/todo-360.png` e `/tmp/todo-1280.png`. A hierarquia é clara e os controles
  permanecem acessíveis. Asserções geométricas confirmaram ausência de rolagem
  horizontal e de sobreposição texto/botão; uma palavra de 200 caracteres quebra
  em várias linhas nas duas larguras.
- **CA8:** as entradas com aparência de HTML permaneceram texto após recarga.
  A execução não encontrou diálogo, erro JavaScript ou destino externo; o
  dashboard também carregou e leu o board com HTTP 200. O README explica uso,
  persistência por origem e limites quando salvar falha.

## Limites

Revisão executada em Chromium, sem validação adicional em Firefox, Safari ou
leitor de tela. A inspeção da árvore acessível e os eventos reais de teclado
cobrem a semântica e os fluxos exigidos, mas não equivalem a uma sessão com
tecnologia assistiva. Não há carregamento remoto que exija um estado de espera.
