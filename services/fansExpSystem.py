import sqlite3
from datetime import *

class ExpSystem:
    @staticmethod
    def getLvlData(userData):
        try:
            with sqlite3.connect('krskKmskBotDb.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT lvl, exp, expToLevel FROM memberLevelData WHERE id = ?', (userData["user_id"],))
                row = cursor.fetchone()
                if row:
                    return row
                # 查不到就自動新增預設
                now = datetime.now()
                cursor.execute(
                    'INSERT INTO memberLevelData (id, nickName, lvl, exp, expToLevel, lastUpdate) VALUES (?, ?, ?, ?, ?, ?)',
                    (userData["user_id"], userData["user_nickName"], 1, 0, 15, now.strftime("%Y-%m-%d/%H:%M:%S"))
                )
                conn.commit()
                return (1, 0, 15)
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def getLastUpdate(userData):
        try:
            with sqlite3.connect('krskKmskBotDb.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT lastUpdate FROM memberLevelData WHERE id = ?', (userData["user_id"],))
                row = cursor.fetchone()
                if row:
                    return row[0]
                # 查不到就自動新增預設
                now = datetime.now()
                cursor.execute(
                    'INSERT INTO memberLevelData (id, nickName, lvl, exp, expToLevel, lastUpdate) VALUES (?, ?, ?, ?, ?, ?)',
                    (userData["user_id"], userData["user_nickName"], 1, 0, 15, now.strftime("%Y-%m-%d/%H:%M:%S"))
                )
                conn.commit()
                return now.strftime("%Y-%m-%d/%H:%M:%S")
        except Exception as e:
            print(e)
            return None
        
    @staticmethod
    def updateExpAndLvl(userData, expAmt, lastUpdate):
        lvlData = ExpSystem.getLvlData(userData)
        user_id = userData["user_id"]
        user_nickName = userData["user_nickName"]
        lvlUp = False
        res = [0, 0, 0]
        if lvlData[1] + expAmt >= lvlData[2]:
            res[0] = lvlData[0] + 1
            res[1] = lvlData[1] + expAmt - lvlData[2]
            res[2] = expToLevel(res[0], lvlData[2])
            lvlUp = True
        else:
            res[0] = lvlData[0]
            res[1] = lvlData[1] + expAmt
            res[2] = lvlData[2]
        # Write into DB
        try:
            with sqlite3.connect('krskKmskBotDb.db') as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE memberLevelData SET nickName = "{user_nickName}", lvl = {res[0]}, exp = {res[1]}, expToLevel = {res[2]}, lastUpdate = "{lastUpdate}"  WHERE id == "{user_id}"')
                conn.commit()
                if lvlUp:
                    return True
        except Exception as e:
            print(e)
            return False
    
    @staticmethod
    def isOverOneMin(lastUpdateTime):
        """
        last_update_time_str: 格式為 'YYYY-MM-DD/HH:MM:SS'
        回傳 (是否超過1分鐘, 新的時間字串)
        """
        # 轉換字串為 datetime 物件
        last_update_time = datetime.strptime(lastUpdateTime, "%Y-%m-%d/%H:%M:%S")
        now = datetime.now()

        # 計算差距
        diff = now - last_update_time
        print(diff)
        if diff.total_seconds() >= 60:
            # 超過一分鐘，建議更新 last_update_time
            return True, now.strftime("%Y-%m-%d/%H:%M:%S")
        else:
            return False, lastUpdateTime

    @staticmethod
    def getUserRank(user_id: str):
        conn = sqlite3.connect('krskKmskBotDb.db')
        cursor = conn.cursor()

        # 1. 抓全部成員的 id, lvl, exp
        cursor.execute("SELECT id, lvl, exp FROM memberLevelData")
        data = cursor.fetchall()
        conn.close()

        # 2. 先依 lvl 再依 exp 排序，兩者皆由大到小
        sorted_data = sorted(data, key=lambda x: (-x[1], -x[2]))  # x=(id, lvl, exp)

        # 3. 排名演算法
        rank = 0
        prev_lvl, prev_exp = None, None
        real_rank = 0
        for idx, (mid, lvl, exp) in enumerate(sorted_data, start=1):
            if (lvl, exp) != (prev_lvl, prev_exp):
                rank = idx
                prev_lvl, prev_exp = lvl, exp
            if mid == user_id:
                real_rank = rank
                break
        return real_rank

# Local Functions
def expToLevel(lvl, curr)-> int:
    if lvl <= 9:
        return int(curr ** 1.1)
    elif lvl <= 30:
        return int(curr ** 1.08)
    elif lvl <= 70:
        return int(curr ** 1.05)
    elif lvl <= 120:
        return int(curr ** 1.02)
    elif lvl <= 200:
        return int(curr ** 1.01)
    
