import sqlite3

class CustomRkCard:
    @staticmethod
    def get_or_create_RGB(id: str, default_r=255, default_g=255, default_b=255):
        try:
            with sqlite3.connect('krskKmskBotDb.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT R, G, B FROM memberCustomSettingData WHERE id = ?', (id,))
                row = cursor.fetchone()
                if row:
                    return row
                # 查不到就自動新增預設
                cursor.execute(
                    'INSERT INTO memberCustomSettingData (id, R, G, B) VALUES (?, ?, ?, ?)',
                    (id, default_r, default_g, default_b)
                )
                conn.commit()
                return (default_r, default_g, default_b)
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def setRGB(id:str, r:int, g:int, b:int) -> bool:
        try:
            CustomRkCard.get_or_create_RGB(id) # do this once to check if no data
            with sqlite3.connect('krskKmskBotDb.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE memberCustomSettingData SET R=?, G=?, B=? WHERE id = ?',
                    (r, g, b, id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
