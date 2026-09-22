# fetch-pr — założenia projektowe

Skill + skrypt do pobierania Pull Requestów z GitHuba na dysk, do analizy
offline. Poniżej decyzje projektowe wypracowane w sesji brainstormingowej i ich
uzasadnienie — do podglądu implementacja: `scripts/fetch-pr.sh` + `SKILL.md`,
przykładowy wynik działania: `example/pr-xawt-cobold-cli-3/` (prawdziwy PR,
łącznie z code review Copilota i wątkiem odpowiedzi).

## Cel

Móc pobrać konkretny PR (metadane, opis, historię commitów, diffy, całą
dyskusję/review) na dysk i odnosić się do niego offline w rozmowie z Claude —
bez trzymania kontekstu w pamięci konwersacji i bez powtarzania zapytań do
GitHub API przy każdej analizie.

## Kluczowe decyzje

**Jednostka pobierania: pojedynczy PR.**
Nie zakres commitów, nie cały branch — jeden konkretny PR na jedno wywołanie.

**Źródło danych: `gh` CLI.**
Zakłada istniejące uwierzytelnienie (`gh auth login`). Bez własnej obsługi
tokenów/HTTP — `gh` już to załatwia i ma dostęp do prywatnych repo.

**Diffy: per-commit, bez zbiorczego diffu całego PR.**
Interesuje nas historia *budowania* zmiany (kolejne commity), nie tylko stan
końcowy. Każdy commit → osobny plik `.diff` z surowym unified diffem
(`gh api -H "Accept: application/vnd.github.v3.diff" .../commits/{sha}`).

**Dyskusja PR: zawsze pobierana, jeden plik na jeden komentarz.**
Ten sam wzorzec co przy diffach — małe, adresowalne jednostki. Dzięki temu
można się odnieść do konkretnego komentarza ("zobacz plik 007") i ocenić go
osobno, zamiast przeszukiwać jeden długi plik. Scalane chronologicznie z 3
źródeł API:
1. **issue comments** — ogólna dyskusja pod PR,
2. **reviews** — podsumowania review (approve / changes requested / comment),
3. **review comments** — komentarze przy konkretnej linii kodu (z `diff_hunk`
   i wątkiem `in_reply_to`).

**Format: JSON dla danych strukturalnych, zwykły tekst/Markdown dla treści.**
Metadane (pola typu data, autor, stan, liczby) → JSON, bo to dane do
łatwego query/grep. Treści z natury tekstowe (opis PR, treść commit message,
treść komentarza, diff) → zwykły tekst, bez zbędnego opakowywania w JSON.

**Katalog wyjściowy: bieżący katalog roboczy, dane traktowane jako tymczasowe.**
Skrypt nic nie przenosi ani nie sprząta automatycznie — to świadoma decyzja,
użytkownik sam decyduje, gdzie i czy chce zachować dany PR na dłużej.

**Implementacja: Bash + `jq`.**
Zero dodatkowych zależności poza `gh`/`jq` (i tak potrzebne przy pracy z `gh`).

**Wywołanie: język naturalny + slash command (`/fetch-pr owner/repo#123`).**

## Struktura wyjściowa

```
pr-<owner>-<repo>-<number>/
  meta.json           # metadane PR: number, title, url, state, author, daty, labels, additions/deletions/changedFiles
  description.md      # surowy opis PR (body), bez modyfikacji
  commits.json         # lista commitów: {oid, messageHeadline, messageBody, authoredDate, authors}, chronologicznie
  diffs/
    001-<shortsha>.diff   # surowy diff pojedynczego commita
    002-<shortsha>.diff
    ...
  discussion/
    001-issue_comment-<autor>.md
    002-review-<stan>-<autor>.md
    003-review_comment-<autor>-<plik>-L<linia>.md
    ...
```

Każdy plik w `discussion/` ma front-matter YAML (`type`, `author`, `created_at`,
a dla `review_comment` dodatkowo `path`, `line`, `in_reply_to` — numer pliku, do
którego dany komentarz jest odpowiedzią, wyliczany automatycznie przez skrypt).

## Napotkany problem po drodze

`gh auth status` potrafi zwrócić exit code 0 nawet gdy token jest już
nieważny (sprawdzone empirycznie na `gh 2.46.0`) — sprawdza tylko, czy dane
logowania są *skonfigurowane*, nie czy faktycznie działają. Skrypt zamiast
tego woła `gh api user`, czyli realny request do API, który faktycznie
wywala się na złym tokenie. Ta sama zasada objęła też `jq` — sam `command -v
jq` nie wystarczy (mógłby wskazywać na zepsuty/podmieniony plik), więc skrypt
dodatkowo odpala trywialny filtr `jq -n '1'`.

## Status

Zaimplementowane i przetestowane end-to-end na prawdziwym PR-cie
(`xawt/cobold-cli#3`, z code review Copilota i wątkiem odpowiedzi — dobry,
wymagający test threadingu `in_reply_to`). Wynik tego testu leży w
`example/pr-xawt-cobold-cli-3/`.
