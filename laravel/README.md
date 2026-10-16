# SmartBank — Laravel + MariaDB

Polska aplikacja bankowa na zaliczenie. Laravel 13, PHP 8.3+, MariaDB, HTML5, CSS3 i Blade. Interfejs inspirowany wcześniejszym SmartBankiem (Flask), którego kod i dokumentacja pozostały w katalogu nadrzędnym. To nowa implementacja; nie przenosi danych z poprzedniej bazy SQLite.

## Uruchomienie

Wymagane: PHP 8.3+ z PDO MySQL, mbstring, XML, ctype, fileinfo, tokenizer, curl; Composer 2 i działająca MariaDB. Do szybkich testów również PDO SQLite. Node.js nie jest potrzebny. Na macOS narzędzia można zainstalować przez `brew install php composer mariadb`, a bazę uruchomić przez `brew services start mariadb`. Na Windows można użyć PHP 8.3+ i MariaDB z lokalnego środowiska; polecenia Artisan są takie same.

W terminalu MariaDB utwórz bazę i użytkownika (zastąp hasło własnym):

```sql
CREATE DATABASE smartbank_laravel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smartbank'@'127.0.0.1' IDENTIFIED BY 'TUTAJ_WLASNE_HASLO';
GRANT ALL PRIVILEGES ON smartbank_laravel.* TO 'smartbank'@'127.0.0.1';
```

Następnie, w katalogu `laravel`:

```sh
composer install
cp .env.example .env
```

W Windows zamiast `cp` można użyć `copy`. Uzupełnij `DB_PASSWORD` i ewentualnie pozostałe `DB_*` w `.env`, następnie:

```sh
php artisan key:generate
php artisan migrate --seed
php artisan serve --host=127.0.0.1 --port=8000
```

Otwórz http://127.0.0.1:8000. Katalogiem publicznym serwera WWW jest wyłącznie `public/`.

## Konta demonstracyjne

| Użytkownik | E-mail | Hasło | Saldo startowe |
|---|---|---|---|
| Administrator | admin@smartbank.test | DemoBank123! | 0 zł |
| Anna Kowalska | anna@smartbank.test | DemoBank123! | 2500 zł |
| Jan Nowak | jan@smartbank.test | DemoBank123! | 1000 zł |

Seeder działa tylko w środowisku `local` i `testing`. Ponowne uruchomienie nie resetuje istniejących sald ani haseł. Zwykła rejestracja tworzy konto z saldem 0 zł. Salda demonstracyjne są wyłącznie danymi początkowymi, a aplikacja nie obsługuje prawdziwych pieniędzy. Rachunki mają format `SB` i 10 cyfr, nie IBAN. Po świeżym seedzie Anna ma `SB0000000002`, a Jan `SB0000000003` (sprawdź faktyczny numer w panelu, jeśli baza zawierała już użytkowników).

## Wymagania zaliczeniowe

| Wymaganie | Implementacja |
|---|---|
| Rejestracja, logowanie, hashowanie hasła | `AuthController`, model `User` z castem `hashed`, sesja Laravel |
| Dwa poziomy uprawnień | `customer`, `admin`; middleware `Administrator` |
| Różne strony po logowaniu | `/home` przekierowuje klienta na pulpit, administratora do listy użytkowników |
| CRUD użytkowników | `AdminUserController`, widoki `admin`, `Route::resource` |
| Lista i szczegóły użytkownika | `/admin/users`, `/admin/users/{user}` |
| Walidacja formularzy i regex | `UserRules`, `BankController`; walidacja po stronie serwera i HTML |
| Przelewy między klientami, sesja | formularz → `transfer_draft` w sesji → potwierdzenie → `TransferService` |
| Saldo i historia | `accounts.balance`, `transfers`, pulpit i historia z paginacją |
| Aktywacja przez e-mail | `MustVerifyEmail`, podpisany link, middleware `verified` |
| SQL Injection | parametryzowane zapytania Eloquent; dane formularzy nie są doklejane do SQL |

Hasła są **hashowane**, nie szyfrowane odwracalnie. Usuwanie użytkownika jest logiczne (`SoftDeletes`): znika z listy, nie może się zalogować, ale pozostaje powiązanie z historią przelewów. Usuwanie wymaga salda 0 zł. Administrator nie może usunąć siebie, zablokować siebie ani odebrać sobie roli. Zmiana e-maila wymaga ponownej aktywacji.

## Poczta i tryb offline

Domyślnie `MAIL_MAILER=log`: wiadomości trafiają do `storage/logs/laravel.log`. Po rejestracji znajdź w tym pliku link `/email/verify/...` i otwórz go w przeglądarce zalogowanej na to samo konto. Link wygasa po 60 minutach. Przycisk ponownej wysyłki generuje nowy. To lokalna demonstracja procesu, **nie dostarczenie wiadomości na skrzynkę**.

Dla prawdziwej wysyłki ustaw dane dostawcy SMTP w `.env`:

```dotenv
MAIL_MAILER=smtp
MAIL_SCHEME=smtp
MAIL_HOST=smtp.twoj-dostawca.pl
MAIL_PORT=587
MAIL_USERNAME=twoj_login
MAIL_PASSWORD=twoje_haslo_aplikacji
MAIL_FROM_ADDRESS=twoj_zweryfikowany_adres
```

Użyj schematu/portu wskazanego przez dostawcę (np. `smtps`/465). Po zmianach wykonaj `php artisan config:clear`. Poprawne `APP_URL` musi wskazywać adres, pod którym odbiorca otwiera aplikację. Wysyłki przez zewnętrzny SMTP nie zweryfikowano — wymaga danych konta pocztowego.

Przed obroną pobierz zależności (`composer install`) i sprawdź działanie MariaDB. Zachowaj lokalny `vendor/`, `.env` i bazę. UI nie używa CDN, zewnętrznych fontów ani bundlera. Po odłączeniu Internetu uruchom MariaDB i `php artisan serve`; dla aktywacji użyj mailera `log`. Nie uruchamiaj ponownie `composer install` podczas obrony. Szczegółowy przewodnik: [OBRONA.md](OBRONA.md).

## Testy

```sh
php artisan test
vendor/bin/pint --test
```

Domyślne testy używają odrębnej bazy SQLite w pamięci. Dla sprawdzenia MariaDB utwórz **odrębną bazę testową**:

```sql
CREATE DATABASE smartbank_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON smartbank_test.* TO 'smartbank'@'127.0.0.1';
```

```sh
DB_CONNECTION=mariadb DB_DATABASE=smartbank_test php artisan test
```

Użytkownik i hasło pochodzą z `.env`. Na PowerShell ustaw `$env:DB_CONNECTION='mariadb'` i `$env:DB_DATABASE='smartbank_test'` przed poleceniem; potem usuń te zmienne z sesji. Testy przebudowują tabele — nigdy nie wskazuj im bazy z danymi do zachowania.

Testy sprawdzają rejestrację, hashowanie, weryfikację podpisu linku, blokady i role, CRUD, potwierdzenie przelewu w sesji, dokładne kwoty, idempotencję, niewystarczające środki, prywatność historii i escaping HTML. Workflow GitHub Actions uruchamia je na MariaDB 11.4 i PHP 8.3.

## Struktura i decyzje

- `routes/web.php` — adresy i middleware dostępu.
- `app/Http/Controllers` — obsługa formularzy, list i przekierowań.
- `app/Models` — użytkownik, rachunek i przelew.
- `app/Services/TransferService.php` — atomowa realizacja przelewu.
- `app/Support/Money.php` — zamiana tekstowej kwoty na całkowite grosze.
- `database/migrations` — schemat bazy; `database/seeders` — dane demonstracyjne.
- `resources/views` i `public/css/bank.css` — HTML Blade i lokalny CSS.

Przelew blokuje użytkowników i rachunki w stałej kolejności (`lockForUpdate`), sprawdza aktualne saldo i stan kont, następnie aktualizuje oba salda i historię w `DB::transaction`. Powtórne użycie UUID zlecenia jest odrzucane. Historia jest filtrowana według rachunku zalogowanego użytkownika. Formularze mają CSRF, sesja jest regenerowana po logowaniu, a logowanie i wysyłanie linków mają limity prób.

## Git

Repozytorium: https://github.com/k0go07022003/smartbank

Wersja Laravel: gałąź `feature/laravel-bank`, katalog `laravel/`. Starszy projekt Flask i jego współautorstwo są zachowane. `.env`, hasła bazy, logi, `vendor/` i dane lokalnej bazy nie trafiają do repozytorium. Termin oddania: ostatnie zajęcia; dokładna data nie została podana.

Źródła techniczne: [Laravel 13](https://laravel.com/docs/13.x), [aktywacja e-mail](https://laravel.com/docs/13.x/verification), [transakcje bazodanowe](https://laravel.com/docs/13.x/database).
