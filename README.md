# CodeFactory

Uma fábrica de software pequena, operada por uma skill do Codex. O estado fica
em arquivos; o dashboard acompanha a produção sem servidor de aplicação.

```text
feature → spec-writer → builder → security / ux / ui / code
                           ↑             ↓
                           └─ CHANGES ─ WAIT FOR ALL
                                         ↓ quatro PASS
                                      approver
                              APPROVE ↙        ↘ ESCALATE
                                main          needs-human
```

São duas rodadas de revisão por ciclo automático. Se a segunda ainda tiver
CHANGES, o job precisa de decisão humana. O builder permanece o mesmo entre
correções; cada rodada tem quatro pareceres sobre o mesmo commit.

## Lista de tarefas web

Para abrir o aplicativo de tarefas, execute na raiz do repositório:

```bash
python3 -m http.server 8001 --bind 127.0.0.1 --directory todo
```

Abra [a lista de tarefas local](http://localhost:8001/). Não há dependências a
instalar nem etapa de build. Escreva uma tarefa e clique em **Adicionar** ou
pressione Enter. Use a caixa de seleção para concluir ou reabrir uma tarefa e o
botão de lixeira para excluí-la. Todos os controles funcionam com teclado;
Tab muda o foco e Espaço alterna a caixa de seleção. Para encerrar o servidor,
pressione Ctrl+C no terminal.

A lista fica no `localStorage`, na chave `codefactory.todo.v1`, somente neste
navegador e nesta origem (protocolo, endereço e porta). Reabrir a mesma URL
mantém as tarefas; outro navegador, endereço ou porta tem uma lista separada.
Não há envio para serviços externos, conta, backup ou sincronização. Limpar os
dados do navegador remove a lista; sessões privadas podem descartá-la ao sair.
Dados salvos inválidos são ignorados e a interface avisa. Se o armazenamento
estiver bloqueado ou sem espaço, os controles continuam funcionando em memória,
mas um aviso informa que as alterações podem ser perdidas ao fechar ou
recarregar a página.

## Usar

Abra uma sessão do Codex neste repositório, com ferramentas de subagentes
disponíveis. Antes do primeiro job, tenha a estrutura inicial commitada em main
e o checkout limpo. A skill é descoberta em `.agents/skills/factory/SKILL.md`.

```text
$factory Criar uma API de tarefas com criação e consulta
$factory next
$factory approve 001-api-de-tarefas
$factory rework 001-api-de-tarefas Corrigir o problema de autorização apontado
```

No cliente que usa `@` para selecionar skills, selecione `@factory` e informe
a operação. `/factory ...` também é entendido como texto pela skill quando
chega ao agente; não depende de registrar um slash command personalizado.

Adicione features como `- [ ] Descrição` em `factory/backlog.md`. `next` reserva
o primeiro item no board antes de marcá-lo. A fábrica executa um job por vez
no checkout compartilhado; resolva um `needs-human` antes de iniciar outro.

## Acompanhar

```bash
python3 -m http.server --directory factory
```

Abra [o dashboard local](http://localhost:8000/dashboard.html). Ele consulta
`board.json` a cada três segundos. Clique em um card para ler os artefatos;
cada rodada mostra os quatro pareceres. O quadro é somente leitura. Não há
dependências externas, telemetria ou publicação em serviço remoto.

## Onde editar

| Arquivo | Papel |
| --- | --- |
| `.agents/skills/factory/SKILL.md` | Orquestração, comandos e loop |
| `.agents/agents/*.md` | Sete contratos de trabalho carregados pelo orquestrador |
| `factory/control.py` | Transições verificáveis e escrita atômica do board |
| `factory/board.json` | Estado durável, identidades, commits e histórico |
| `factory/jobs/<id>/` | Spec, build, pastas round-N e decisão |
| `factory/dashboard.html` | Interface autocontida |

Os contratos Markdown são lidos explicitamente ao criar os subagentes; não são
configurações nativas TOML. Os modelos são herdados da sessão. Os quatro
revisores executam conforme as vagas disponíveis, inclusive em lotes. O builder
fica parado até todos terminarem.

O helper é chamado **somente pelo orquestrador**, da raiz do repo, com operações
`new`, `spec`, `agent`, `built`, `collect`, `decide`, `rework`, `human-approve` e
`merged`; `python3 factory/control.py --help` mostra os argumentos. Ele não cria
agentes, executa testes de features nem faz merge. Essas ações pertencem à skill.
Há um único orquestrador por checkout; não execute operações simultâneas.

Pareceres começam com `VERDICT: PASS` ou `VERDICT: CHANGES`. Decisões começam
com `APPROVE` ou `ESCALATE`. Em ambos, a segunda linha é `COMMIT: <SHA completo>`
e o restante contém evidências. Arquivo ausente mantém a rodada pendente;
arquivo inválido ou commit divergente impede a transição.

O merge automático exige quatro PASS e APPROVE para o commit congelado.
`approve` registra uma exceção humana explícita, preservando os pareceres.
`rework` abre outro ciclo de duas rodadas sem sobrescrever as anteriores.
Se main divergir, o merge fast-forward para e exige resolução; não há push
automático. Interrupções são retomadas pelo board e pelos arquivos. Se o runtime
não recuperar o builder, a substituição fica registrada com o motivo.

## Verificar a fábrica

Requisitos: Python 3 e Git. O dashboard roda diretamente no navegador.

```bash
python3 -m unittest discover -s factory -p 'test_*.py'
```

Os testes usam repositórios Git temporários para exercitar a barreira de quatro
pareceres, correções, limite de rodadas, commits divergentes, autorização e merge,
aprovação humana, backlog e recuperação do builder. Não executam features reais
nem usam uma API paga. A qualidade semântica dos pareceres continua sendo
responsabilidade dos agentes e do approver.
