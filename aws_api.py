from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from fastapi.responses import FileResponse
import subprocess
import os


app = FastAPI(title="Smart Farm Weather API", version="1.0.0")

# CORS 설정 (외부에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 연결 설정
DB_CONFIG = {
    "host": "localhost",
    "database": "aws_log",
    "user": "hyejin",
    "password": "smartfarm"  # 실제 비밀번호로 변경
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# 응답 모델
class WeatherData(BaseModel):
    timestamp: datetime
    temp: Optional[float]
    humid: Optional[float]
    radn: Optional[float]
    wind_degree: Optional[float]
    wind: Optional[float]
    rainfall: Optional[float]
    battery: Optional[float]


class WeatherStats(BaseModel):
    avg_temp: Optional[float]
    max_temp: Optional[float]
    min_temp: Optional[float]
    avg_humid: Optional[float]
    total_rainfall: Optional[float]
    avg_radn: Optional[float]
    data_count: int


# 1. 헬스 체크
@app.get("/")
def read_root():
    return {
        "message": "Smart Farm Weather API",
        "version": "1.0.0",
        "endpoints": {
            "latest": "/api/weather/latest",
            "today": "/api/weather/today",
            "date": "/api/weather/date/{date}",
            "range": "/api/weather/range",
            "stats": "/api/weather/stats"
        }
    }


# 2. 최신 데이터 조회
@app.get("/api/weather/latest", response_model=WeatherData)
def get_latest_weather():
    """가장 최근 기상 데이터 1개 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="데이터가 없습니다")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. 오늘 데이터 조회
@app.get("/api/weather/today", response_model=List[WeatherData])
def get_today_weather():
    """오늘 날짜의 모든 기상 데이터 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            WHERE DATE(timestamp) = CURRENT_DATE
            ORDER BY timestamp DESC
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail="오늘 데이터가 없습니다")

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. 특정 날짜 데이터 조회
@app.get("/api/weather/date/{date}", response_model=List[WeatherData])
def get_weather_by_date(date: str):
    """
    특정 날짜의 기상 데이터 조회
    date 형식: YYYY-MM-DD (예: 2024-11-02)
    """
    try:
        # 날짜 형식 검증
        datetime.strptime(date, "%Y-%m-%d")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp DESC
        """, (date,))
        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail=f"{date} 데이터가 없습니다")

        return results
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5. 날짜 범위 데이터 조회
@app.get("/api/weather/range", response_model=List[WeatherData])
def get_weather_by_range(
        start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
        end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
        limit: int = Query(1000, description="최대 조회 개수")
):
    """날짜 범위로 기상 데이터 조회"""
    try:
        # 날짜 형식 검증
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            WHERE DATE(timestamp) BETWEEN %s AND %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (start_date, end_date, limit))
        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail="해당 기간의 데이터가 없습니다")

        return results
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 6. 통계 데이터 조회
@app.get("/api/weather/stats", response_model=WeatherStats)
def get_weather_stats(
        start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    """
    기상 데이터 통계 조회
    날짜 미지정 시 오늘 데이터 기준
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if start_date and end_date:
            # 날짜 범위 지정
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            query = """
                SELECT 
                    AVG(temp) as avg_temp,
                    MAX(temp) as max_temp,
                    MIN(temp) as min_temp,
                    AVG(humid) as avg_humid,
                    SUM(rainfall) as total_rainfall,
                    AVG(radn) as avg_radn,
                    COUNT(*) as data_count
                FROM weather_data
                WHERE DATE(timestamp) BETWEEN %s AND %s
            """
            cur.execute(query, (start_date, end_date))
        else:
            # 오늘 데이터
            query = """
                SELECT 
                    AVG(temp) as avg_temp,
                    MAX(temp) as max_temp,
                    MIN(temp) as min_temp,
                    AVG(humid) as avg_humid,
                    SUM(rainfall) as total_rainfall,
                    AVG(radn) as avg_radn,
                    COUNT(*) as data_count
                FROM weather_data
                WHERE DATE(timestamp) = CURRENT_DATE
            """
            cur.execute(query)

        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result or result['data_count'] == 0:
            raise HTTPException(status_code=404, detail="통계 데이터가 없습니다")

        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 7. 최근 N시간 데이터 조회
@app.get("/api/weather/recent", response_model=List[WeatherData])
def get_recent_weather(hours: int = Query(24, description="최근 몇 시간")):
    """최근 N시간의 기상 데이터 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            WHERE timestamp >= NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
        """, (hours,))
        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            raise HTTPException(status_code=404, detail=f"최근 {hours}시간 데이터가 없습니다")

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 8. 특정 조건으로 데이터 조회 (일조량 부족한 날)
@app.get("/api/weather/low-light", response_model=List[WeatherData])
def get_low_light_days(
        threshold: float = Query(100, description="일조량 임계값 (W/m²)"),
        days: int = Query(7, description="최근 며칠")
):
    """일조량이 낮은 날의 데이터 조회 (보광 결정용)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM weather_data 
            WHERE radn < %s 
            AND DATE(timestamp) >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY timestamp DESC
        """, (threshold, days))
        results = cur.fetchall()
        cur.close()
        conn.close()

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/generate")
def generate_weather_graph(days: int = 7):
    """기상 데이터 그래프 생성"""
    try:
        # 그래프 생성 스크립트 실행
        result = subprocess.run(
            ['python3', 'aws_graph.py'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"message": "그래프 생성 완료", "path": "./graphs/"}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/image/{graph_type}")
def get_graph_image(graph_type: str):
    """
    생성된 그래프 이미지 반환
    graph_type: separate, combined, daily
    """
    file_path = f"./graphs/weather_{graph_type}.png"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="그래프 이미지가 없습니다")

    return FileResponse(file_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)