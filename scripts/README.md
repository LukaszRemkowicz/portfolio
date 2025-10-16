# Portfolio Scripts

Skrypty administracyjne dla portfolio.

## 🚀 deploy.sh

Automatyczny skrypt deployment na serwer produkcyjny.

### Jak używać:

#### 1. Skonfiguruj skrypt:
```bash
# Edytuj ścieżkę w pliku:
nano scripts/deploy.sh

# Zmień tę linię:
PROJECT_DIR="/path/to/portfolio"  # ZMIEŃ NA SWOJĄ ŚCIEŻKĘ!
```

#### 2. Zrób skrypt wykonywalnym:
```bash
chmod +x scripts/deploy.sh
```

#### 3. Uruchom ręcznie (test):
```bash
./scripts/deploy.sh
```

#### 4. Dodaj do crontab:
```bash
# Edytuj crontab:
crontab -e

# Dodaj linię (co 10 minut):
*/10 * * * * /path/to/portfolio/scripts/deploy.sh

# Lub co 15 minut:
*/15 * * * * /path/to/portfolio/scripts/deploy.sh
```

### Co robi skrypt:

1. **Sprawdza** czy są nowe zmiany w git
2. **Pobiera** kod z branch `main`
3. **Zatrzymuje** istniejące kontenery
4. **Buduje** nowe obrazy Docker
5. **Uruchamia** nowe kontenery
6. **Sprawdza** czy wszystko działa
7. **Czyści** stare obrazy
8. **Loguje** wszystko do `/var/log/portfolio-deploy.log`

### Logi:

```bash
# Zobacz logi deployment:
tail -f /var/log/portfolio-deploy.log

# Ostatnie 50 linii:
tail -50 /var/log/portfolio-deploy.log
```

### Troubleshooting:

#### Problem: "Katalog projektu nie istnieje"
```bash
# Sprawdź ścieżkę w skrypcie:
grep "PROJECT_DIR" scripts/deploy.sh

# Zmień na właściwą ścieżkę
```

#### Problem: "Docker nie jest dostępny"
```bash
# Sprawdź czy Docker działa:
docker --version
docker-compose --version
# lub
docker compose version
```

#### Problem: "Nie można pobrać kodu"
```bash
# Sprawdź połączenie z GitHub:
git fetch origin

# Sprawdź uprawnienia:
ls -la .git/
```

### Przykład użycia:

```bash
# 1. Skonfiguruj:
PROJECT_DIR="/home/user/portfolio"

# 2. Test:
./scripts/deploy.sh

# 3. Cron (co 10 minut):
*/10 * * * * /home/user/portfolio/scripts/deploy.sh

# 4. Sprawdź logi:
tail -f /var/log/portfolio-deploy.log
```

### Bezpieczeństwo:

- ✅ Skrypt sprawdza czy kod się zmienił
- ✅ Nie robi deployment jeśli brak zmian
- ✅ Loguje wszystkie operacje
- ✅ Zatrzymuje się przy błędach (`set -e`)
- ✅ Sprawdza status kontenerów

### Wymagania:

- Git
- Docker
- Docker Compose
- Uprawnienia do katalogu projektu
- Połączenie z internetem (git pull)
