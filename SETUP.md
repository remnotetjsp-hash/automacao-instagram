# Automação de posts — Instagram @adv.leonardorezende

Funcionamento: os posts ficam em `media/`, a agenda fica em `queue/fila.csv` e o GitHub Actions
(grátis) roda `scripts/publish.py` a cada 15 minutos, publicando o que estiver na hora.
Depois do setup, nada precisa ser feito no Instagram.

## Setup (uma vez, ~45 min)

1. **Conta Profissional:** no Instagram, Configurações → Tipo de conta e ferramentas →
   Mudar para conta profissional (Empresa ou Criador).
2. **App na Meta:** developers.facebook.com → Criar app → caso de uso de Instagram
   ("API do Instagram com login do Instagram"). Adicionar as permissões
   `instagram_business_basic` e `instagram_business_content_publish`.
3. **Testador:** no app, adicionar a própria conta como "Testador do Instagram" e aceitar o convite
   no Instagram (Configurações → Apps e sites → Convites de testador).
4. **Token:** gerar o token de acesso da conta no painel do app. Anotar também o ID da conta Instagram.
   O token dura 60 dias (renovar na virada do mês).
5. **GitHub:** criar um repositório **público** com o conteúdo desta pasta.
   Em Settings → Secrets and variables → Actions, criar `IG_USER_ID` e `IG_TOKEN`.
6. **Teste:** colocar 1 linha na fila para daqui a 20 min e rodar o workflow manualmente
   (Actions → publicar-instagram → Run workflow).

## Formato da fila (`queue/fila.csv`)

`id, datetime (hora de São Paulo, ex. 2026-10-06T09:00:00), tipo (imagem|reel), arquivo (caminho dentro de media/), legenda, status, post_id, tentativas, erro`

Status começa como `pendente`; o publicador troca para `publicado` ou `erro` (tenta até 3 vezes).

## Limites e cuidados

- A API aceita ~100 publicações por 24h; aqui são 25 por dia.
- O repositório é público: o conteúdo agendado fica visível antes de ser postado.
- O horário do GitHub pode atrasar alguns minutos.
- Antes de ligar tudo: revisar legendas e citações jurídicas (Provimento 205/2021 da OAB).
