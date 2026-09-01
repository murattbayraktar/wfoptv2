Sentetik eğitim CSV'si üretir (bank_forecast/scripts/generate_training_csv.py).

Kullanım: /generate-training-csv <başlangıç YYYY-MM-DD> <bitiş YYYY-MM-DD> <satır sayısı> [ek argümanlar]

$ARGUMENTS içindeki ilk üç değeri sırasıyla --start, --end, --count olarak
kullan. Fazladan argüman varsa (örn. `--output ...`, `--seed ...`,
`--include-weekends`, `--include-holidays`) olduğu gibi ekle.

Eğer $ARGUMENTS boşsa veya ilk üç değer eksikse, kullanıcıya başlangıç
tarihi, bitiş tarihi ve üretilecek satır sayısını sor; tahmin etme.

Şu komutu bank_forecast dizininde (venv aktifken, yoksa `venv/bin/python3`
kullanarak) çalıştır ve çıktısını kullanıcıya göster:

    python3 scripts/generate_training_csv.py --start <start> --end <end> --count <count> [ek argümanlar]

Üretilen CSV, şu kolonları içerir: Reference, TaskType, SubTaskType,
OrderDate, DispatcherMainPortfolio, FirstForwardOmDate,
OperatorMainPortfolio, EntryProcessCount. Tüm zaman damgaları 08:00-18:00
arasına dağıtılır ve varsayılan olarak yalnızca iş günlerini (hafta sonu ve
Türkiye resmi tatilleri hariç) kullanır.

TaskType, SubTaskType, DispatcherMainPortfolio ve OperatorMainPortfolio
değer kümeleri script içinde (dosyanın başındaki sabitler) tanımlıdır;
kullanıcı yeni bir değer eklemek isterse `bank_forecast/scripts/generate_training_csv.py`
dosyasındaki TASK_TYPES / SUB_TASK_TYPES / DISPATCHER_TEAMS / OPERATOR_TEAMS
listelerini güncelle.
