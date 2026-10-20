# Especificação — 001-todo-list

## Pedido e resultado

Pedido original salvo em `factory/board.json`: **“Cria um simples app de todo list web.”**

Entregar uma página web em português na qual uma pessoa possa anotar tarefas, marcar o que concluiu e excluir o que não precisa mais, usando um navegador local.

## Escopo e premissas

- Aplicação pequena, estática e de uso individual, com HTML, CSS e JavaScript nativos. O repositório já usa HTML autocontido e não tem framework, manifesto de frontend ou aplicação de tarefas existente. Não há necessidade de introduzir uma cadeia de build.
- Disponibilizar a aplicação em `todo/index.html`, com instruções no README para servir essa pasta. Arquivos auxiliares dentro de `todo/` são permitidos se ajudarem a manutenção.
- Incluir criação, conclusão/reabertura e exclusão de tarefas. Como premissa de utilidade básica, guardar tarefas e estados no próprio navegador com `localStorage`.
- Não estão no escopo contas, backend, sincronização, colaboração, edição de texto, filtros, prioridades, datas, instalação como aplicativo ou publicação remota.
- Não há decisão de produto pendente que impeça a implementação. A identidade visual pode ser decidida pelo builder, respeitando legibilidade e simplicidade.

## Critérios de aceitação

1. **Acesso:** seguindo o comando documentado, `http://localhost:8001/` abre a aplicação de tarefas. O título da página, o título principal e as instruções da interface estão em português; nenhuma instalação de dependência ou etapa de build é necessária.
2. **Criar:** escrever uma tarefa e enviar pelo botão ou por Enter adiciona exatamente um item pendente com o texto informado, removendo espaços externos. O campo fica pronto para a próxima tarefa. Texto vazio ou composto somente por espaços não cria itens e tem uma indicação compreensível de validação.
3. **Concluir e reabrir:** cada tarefa pode alternar entre pendente e concluída. O estado é perceptível pelo controle e pela apresentação do texto, sem depender apenas de cor. Alterar uma tarefa não altera as demais, mesmo quando seus textos são iguais.
4. **Excluir e estado vazio:** é possível excluir individualmente uma tarefa pendente ou concluída. Somente o item escolhido desaparece. A lista vazia apresenta orientação curta para criar a primeira tarefa, inclusive após excluir o último item.
5. **Guardar localmente:** após criar, concluir ou excluir, recarregar a página mantém a lista resultante no mesmo navegador e origem. Armazenamento indisponível ou conteúdo salvo inválido não impede o uso dos controles básicos; quando não for possível salvar, a interface informa que as alterações podem ser perdidas. Não enviar tarefas para serviços externos.
6. **Teclado e semântica:** o formulário tem rótulo acessível para o campo; todos os controles funcionam com teclado, têm nomes que permitem identificar sua ação e apresentam foco visível. A ordem de foco é lógica; excluir o elemento focado deixa um destino de foco útil. A página declara idioma e viewport.
7. **Apresentação:** a 360 px e a 1280 px de largura, o conteúdo principal e seus controles ficam utilizáveis sem rolagem horizontal. Textos longos, inclusive uma palavra de 200 caracteres, quebram sem cobrir controles. Há hierarquia visual clara, contraste legível e distinção entre ações de adicionar, concluir e excluir.
8. **Texto seguro e integração:** o texto de tarefas é tratado como texto, nunca como HTML executável. A implementação não requer CDN, telemetria, credenciais ou chamadas de rede além dos arquivos locais. O README explica como iniciar e usar a aplicação, a persistência local e sua limitação quando o armazenamento falha. A fábrica e seu dashboard continuam funcionando sem alterações de comportamento.

## Repositório e convenções inspecionados

- `README.md`: documentação em português; execução estática com `python3 -m http.server`; comandos de verificação da fábrica.
- `factory/dashboard.html`: exemplo existente de HTML, CSS e JavaScript nativos, `lang="pt-BR"`, viewport responsivo, controles semânticos e inserção segura por `textContent`/nós DOM.
- `factory/control.py` e `factory/test_control.py`: Python de biblioteca padrão e testes `unittest` da orquestração; não são backend da nova aplicação.
- `factory/board.json`: fonte do pedido deste job. Não deve ser usado como armazenamento de tarefas.
- `.agents/agents/spec-writer.md`: contrato deste artefato. Não foi encontrado `AGENTS.md`, manifesto frontend nem teste de aplicação web existente.
- Arquivos de produto esperados: `todo/index.html`, possíveis auxiliares sob `todo/` e a seção pertinente do `README.md`. Preservar a implementação da fábrica.

## Verificação

Executar a partir da raiz do repositório:

```bash
python3 -m unittest discover -s factory -p 'test_*.py'
python3 -m http.server 8001 --bind 127.0.0.1 --directory todo
```

O primeiro comando verifica a regressão da fábrica (CA8). O segundo fica em execução durante as verificações manuais. Abrir `http://localhost:8001/` em um navegador; interromper o servidor com Ctrl+C ao terminar. Não confundir o resultado dos testes Python com evidência das interações web.

| Critérios | Verificação manual observável |
| --- | --- |
| CA1, CA8 | Seguir o README em um checkout sem dependências frontend; abrir a URL, conferir título/idioma e aba Network sem serviços externos. Servir também `factory/` em outra porta, se necessário, e abrir o dashboard para confirmar que continua legível. |
| CA2 | Adicionar `Comprar pão` pelo botão e `Estudar` por Enter; conferir uma inserção por envio e campo pronto para reutilizar. Enviar campo vazio e depois três espaços: a quantidade não muda e há orientação. |
| CA3, CA4 | Criar duas tarefas com o mesmo texto; concluir e reabrir somente uma. Excluir a outra e confirmar identidade correta; excluir todos os itens e conferir o estado vazio. |
| CA5 | Criar duas tarefas, concluir uma, recarregar e conferir textos/estados. Excluir uma, recarregar e conferir que não retorna. Nas ferramentas do navegador, identificar a chave usada e substituir seu conteúdo por JSON inválido; recarregar e confirmar que é possível criar tarefas. Simular `localStorage.setItem` lançando erro via DevTools ou bloquear armazenamento para a origem; confirmar uso em memória e aviso de persistência. |
| CA6 | Usar Tab, Shift+Tab, Enter e Espaço para criar, concluir, reabrir e excluir. Conferir foco visível, destino útil após exclusão e nomes/rótulos na árvore de acessibilidade do navegador. |
| CA7 | Conferir a página a 360 × 800 e 1280 × 800, com tarefas pendentes, concluídas e texto longo. Criar uma palavra de 200 caracteres e verificar quebra e acesso aos controles. Conferir legibilidade e estado concluído sem depender de cor. |
| CA8 | Adicionar literalmente `<img src=x onerror=alert(1)>` e `<script>alert(1)</script>`: ambos aparecem como texto, sem diálogo, elemento injetado ou execução; recarregar e repetir a inspeção. Ler os pontos de renderização e persistência do código para confirmar o tratamento seguro. |

Os cenários de navegador são a verificação funcional desta página pequena; registrar no build quais foram realmente executados e qualquer limitação do ambiente. Não é necessário adicionar testes que apenas repitam a implementação.

## Segurança, UX e UI

**Segurança:** os dados são locais ao navegador e à origem; não há autenticação, permissões de servidor ou segredos a implementar. Renderização segura, leitura defensiva do armazenamento e ausência de envio externo se aplicam. O conteúdo local não deve ser apresentado como backup ou sincronização.

**UX:** o fluxo principal precisa ser imediato, com suporte a Enter, retorno de validação, estado vazio útil, distinção entre pendente e concluída e comportamento claro quando a persistência falha. Excluir é uma ação individual simples; não é necessário um modal de confirmação.

**UI:** formulário e lista devem formar uma hierarquia clara, responsiva, com tipografia legível, foco visível e controles reconhecíveis. Imagens, ilustrações, animações e sistemas de design externos não são necessários para o resultado pedido.
