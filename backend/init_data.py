#!/usr/bin/env python3
"""
프로젝트 초기 데이터 설정 스크립트
순서: delete_and_recreate.py -> seed_data.py -> recipe_rag_pipeline.py
"""

import subprocess
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_name):
    """스크립트를 실행하고 결과를 반환"""
    try:
        logger.info(f"🔄 {script_name} 실행 중...")
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        logger.info(f"✅ {script_name} 실행 완료")
        if result.stdout:
            logger.info(f"출력: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {script_name} 실행 실패: {e}")
        if e.stdout:
            logger.error(f"표준 출력: {e.stdout}")
        if e.stderr:
            logger.error(f"에러 출력: {e.stderr}")
        return False

def main():
    """메인 실행 함수"""
    logger.info("🚀 프로젝트 초기 데이터 설정 시작")
    
    scripts = [
        "delete_and_recreate.py",
        "seed_data.py", 
        "recipe_rag_pipeline.py"
    ]
    
    for i, script in enumerate(scripts, 1):
        logger.info(f"📋 단계 {i}/{len(scripts)}: {script}")
        
        if not run_script(script):
            logger.error(f"💥 {script} 실행 실패로 인해 초기화를 중단합니다.")
            sys.exit(1)
        
        # 스크립트 간 잠시 대기
        if i < len(scripts):
            logger.info("⏳ 다음 단계 준비 중... (3초 대기)")
            time.sleep(3)
    
    logger.info("🎉 모든 초기 데이터 설정이 완료되었습니다!")

if __name__ == "__main__":
    main() 