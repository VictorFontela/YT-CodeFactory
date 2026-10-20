# Build — 001-todo-list

## Implementação inicial — 2026-10-20

Aplicação estática em português em `todo/index.html`, com CSS e JavaScript
locais, sem dependências, build, backend ou publicação. É possível criar por
botão/Enter, concluir/reabrir e excluir tarefas com identidade própria, inclusive
textos repetidos. A lista vazia orienta o primeiro uso. O formulário valida texto
em branco, remove espaços externos e devolve o foco ao campo.

A persistência usa `localStorage`, chave `codefactory.todo.v1`. A leitura valida
estrutura, tipos e unicidade dos IDs antes de carregar qualquer item. JSON ou
conteúdo inválido resulta em lista nova com aviso. Falhas de leitura/escrita são
tratadas e os controles continuam disponíveis em memória com aviso sobre perda
de alterações. Textos são inseridos por `textContent`; nenhum dado de tarefa é
interpretado como HTML ou enviado para serviços externos.

O layout usa uma coluna central, formulário que se empilha em telas pequenas,
quebra de palavras longas, caixas de seleção nativas, texto riscado no estado
concluído e botões individuais com nomes acessíveis. Há foco visível e destino
de foco após exclusão: próxima tarefa, anterior ou campo de criação. O README
documenta execução, uso, origem dos dados e limites da persistência.

Arquivos de produto alterados: `todo/index.html`, `todo/style.css`, `todo/app.js`
e `README.md`. Nenhum código, teste ou dashboard da fábrica foi alterado.

## Comandos e resultados reais

Executados na raiz do repositório:

```bash
node --check todo/app.js
python3 -m unittest discover -s factory -p 'test_*.py'
git diff --check
python3 -m http.server 8001 --bind 127.0.0.1 --directory todo
python3 -m http.server 8002 --bind 127.0.0.1 --directory factory
curl --fail --silent --show-error http://127.0.0.1:8001/
node /tmp/todo-browser-check.cjs
```

- Sintaxe JavaScript: exit 0.
- Fábrica: **16 testes, OK**, exit 0.
- Verificação de espaços do diff: exit 0.
- Servidor da aplicação e servidor do dashboard iniciados; HTTP da aplicação
  respondeu com o HTML esperado. Ambos são encerrados no fim do build.
- Verificação funcional em **Chromium 156.0.8078.4 / Playwright 1.64.1**: exit 0;
  todos os cenários abaixo passaram. A automação usa navegador real, eventos de
  teclado, recargas, árvore acessível, inspeção da geometria e screenshots.
  Script de QA temporário em `/tmp/todo-browser-check.cjs`, sem adicionar
  dependências ao produto ou ao repositório.

O ambiente inicialmente não tinha navegador nem Playwright. A primeira tentativa
npm falhou com `EAI_AGAIN` e o servidor no sandbox falhou com `PermissionError`.
Após escaladas aprovadas, Playwright e Chromium foram baixados. A primeira
inicialização do Chromium identificou `libatk-1.0.so.0` ausente; a instalação
padrão das bibliotecas de sistema foi aprovada e concluiu com exit 0. Preparação:

```bash
npm exec --yes --cache /tmp/todo-npm-cache --package=@playwright/test -- playwright --version
npm exec --yes --cache /tmp/todo-npm-cache --package=@playwright/test -- playwright install chromium
npm exec --yes --cache /tmp/todo-npm-cache --package=@playwright/test -- playwright install-deps chromium
```

As falhas iniciais eram do ambiente e foram resolvidas antes da verificação
funcional. Esses pacotes são somente ferramentas de QA; para usar a aplicação
basta o servidor Python documentado.

## Critérios e evidências

| Critério | Evidência executada e resultado |
| --- | --- |
| CA1 — acesso | Navegação real para `http://localhost:8001/`, título `Minha lista de tarefas`, `lang="pt-BR"`, viewport presente; HTML e arquivos locais carregaram. Inspeção da página confirma títulos/instruções em português. |
| CA2 — criar | Envio vazio e com três espaços mantém zero itens e mostra validação. `  Comprar pão  ` pelo botão e `Estudar` por Enter resultam em exatamente dois itens com texto esperado, campo vazio e focado. |
| CA3 — concluir/reabrir | Duas tarefas `igual` mantêm identidades independentes. Concluir/reabrir uma preserva a outra; checkbox e classe de texto riscado correspondem ao estado. |
| CA4 — excluir/vazio | Exclusão individual pendente/concluída e de uma duplicata remove apenas o alvo. Excluir todos retorna o estado vazio e o foco ao campo. |
| CA5 — guardar | Criar duas, concluir uma e recarregar preserva textos/estados; excluir e recarregar mantém exclusão. JSON inválido, objeto em vez de array, tipo de estado inválido e IDs duplicados são rejeitados com aviso, permitindo nova criação. `Storage.prototype.setItem` forçado a lançar `QuotaExceededError` mantém criação/conclusão/exclusão em memória com aviso. Getter de `localStorage` forçado a lançar `SecurityError` também mantém todos esses controles. |
| CA6 — teclado/semântica | Localizadores da árvore acessível encontram campo por rótulo, checkbox por texto e exclusão por ação/texto. Tab/Shift+Tab, Enter e Espaço foram exercitados; após excluir com teclado o foco vai à próxima tarefa e, ao excluir a última, ao campo. Foco de teclado tem outline sólido; inspecionados HTML semântico, ordem e árvore acessível. |
| CA7 — apresentação | Viewports reais 360×800 e 1280×800, com tarefas pendentes/concluídas e palavra de 200 caracteres. Asserções confirmam ausência de overflow horizontal, controles fora da viewport e sobreposição texto/botão; palavra quebra em várias linhas. Screenshots `/tmp/todo-360.png` e `/tmp/todo-1280.png` visualmente inspecionados. Contrastes calculados: texto principal 11,78:1, texto secundário no branco 5,15:1, rodapé 4,68:1, botão principal 6,92:1. |
| CA8 — segurança/integração | `<img src=x onerror=alert(1)>` e `<script>alert(1)</script>` aparecem literalmente antes/depois de recarregar, com zero nós img/script injetados, zero diálogos e zero erros JavaScript. Observação de requisições encontrou zero destinos externos. Dashboard em `http://localhost:8002/dashboard.html` abriu, consultou `board.json` com HTTP 200 e foi inspecionado visualmente em `/tmp/todo-factory-dashboard.png`. Os 16 testes da fábrica passaram. |

## Limitações

- Nenhum bloqueador pendente. QA funcional e visual foi realizado em Chromium;
  não foi feita execução adicional em Firefox/Safari nem com leitor de tela.
- Screenshots e script de QA em `/tmp` são evidência desta sessão, não artefatos
  versionados nem requisito de execução da aplicação.
- Persistência é local à origem e ao navegador; não há backup ou sincronização,
  conforme escopo. Quando o armazenamento falha, a lista continua em memória.

## Correções

Nenhuma rodada de correção agendada até este build inicial.
