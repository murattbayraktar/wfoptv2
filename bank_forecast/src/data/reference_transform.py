import pandas as pd


def build_dispatcher_operator_views(df: pd.DataFrame) -> pd.DataFrame:
    """Ham referans (talimat) satırlarını, her ekibin kendi göreceği zaman
    diliminde bir 'olay' olarak göreceği uzun formata dönüştürür.

    Kurallar:
    - Karşılayıcı (dispatcher) görünümü: HER satır, `order_date` baz alınarak sayılır.
    - İşlemci (operator) görünümü: yalnızca `dispatcher_team != operator_team`
      VE `first_forward_date` dolu olan satırlar, `first_forward_date` baz
      alınarak AYRICA sayılır.
    - Karşılayıcı == işlemci olduğunda satır yalnızca dispatcher görünümünde
      bulunur (mükerrer sayım önlenir). Henüz yönlendirilmemiş
      (`first_forward_date` boş) satırlar da yalnızca dispatcher görünümünde
      bulunur.

    Girdi kolonları: `dispatcher_team, operator_team, order_date,
    first_forward_date, transaction_type` (+ varsa `entry_process_count`,
    `reference` — olduğu gibi taşınır).

    Döner: `team`, `event_time` kolonları eklenmiş, dispatcher+operator
    görünümleri birleştirilmiş (concat) dataframe. `count` hesaplamaz —
    bu karar çağıran tarafa (metrik tipine göre) bırakılır.
    """
    dispatcher_view = df.copy()
    dispatcher_view["team"] = dispatcher_view["dispatcher_team"]
    dispatcher_view["event_time"] = dispatcher_view["order_date"]

    operator_eligible = df[
        (df["dispatcher_team"] != df["operator_team"]) & df["first_forward_date"].notna()
    ].copy()
    operator_eligible["team"] = operator_eligible["operator_team"]
    operator_eligible["event_time"] = operator_eligible["first_forward_date"]

    combined = pd.concat([dispatcher_view, operator_eligible], ignore_index=True)
    return combined
