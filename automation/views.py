from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import json
import os
import time


@csrf_exempt  # API 테스트를 위해 임시로 CSRF 보호를 비활성화 (DRF를 사용하면 더 안전하게 처리 가능)
def apply_discount_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        car_number = data.get('car_number')

        load_dotenv() # .env 파일에서 환경 변수를 불러옴

        if not car_number:
            return JsonResponse({"message": "차량 번호를 확인 해주세요.","resultCode":0}, status=400)

        LOGIN_ID = os.environ.get("PARKING_ID")
        LOGIN_PW = os.environ.get("PARKING_PW")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # 1. 원래 사이트(주차 사이트) 에서 시작
                page.goto("https://parking.bcits.go.kr/main/main.do")

                page.click("a[href='/user/login.do']")

                # 3. 통합로그인(SSO) 페이지로 넘어갈 때까지 기다림
                #    ID 입력창이 보일 때까지 기다리는 것이 가장 확실합니다.
                page.wait_for_selector("input[name=login_id]")
                print("통합로그인 페이지로 이동 완료.")
                # 4. 통합로그인 페이지에서 ID와 비밀번호 입력 후 로그인
                page.fill("input[name=login_id]", LOGIN_ID)
                page.fill("input[name=login_pwd]", LOGIN_PW)

                time.sleep(1)
                page.click("a[onclick='loginProc()']")
                print("통합로그인 시도.")

                # 5. 다시 원래 사이트로 돌아올 때까지 기다림
                #    '로그아웃' 버튼이 보이면 로그인이 성공한 것입니다.
                page.wait_for_selector("div.ico_login[style*='display: block']")
                print("주차 사이트로 복귀 및 로그인 성공.")

                # 6. 이제 소상공인 할인 페이지 이동
                page.goto("https://parking.bcits.go.kr/smallbiz/select_smallbiz_car.do")

                # 차량 번호 입력
                page.fill("input#carNo", car_number)
                page.click("a#carList")

                result_message = "차량 번호 검색 "

                if page.is_visible('tbody.car-number_list:has-text("조회된 데이터가 없습니다.")'):
                    result_message = "차량 조회 실패: 등록되지 않은 차량입니다. 다시 확인해주세요."
                    result_code = 0
                else:
                    # 3. 데이터가 있다면, 결과 행(tr)의 개수를 셈
                    rows = page.locator("tbody.car-number_list tr")
                    row_count = rows.count()
                    print(f"조회된 차량 개수: {row_count}대")

                    if row_count > 1:
                        # 3-1. 결과가 1개보다 많으면 중복으로 판단
                        result_message = "중복된 차량 번호가 조회되었습니다. 관리자에게 문의해주세요. !!!"
                        result_code = 100

                    elif row_count == 1:
                        # 3-2. 결과가 정확히 1개일 경우에만 할인 진행
                        print("정상 차량 조회 완료. 할인을 진행합니다.")

                        # 더 안정적인 방법: 찾은 행(rows) 안에서 할인 버튼을 찾아 클릭
                        rows.locator("button.discountBtn").click()
                        print("주차 할인 버튼 선택 완료")

                        page.click("button#alertPopConfirm")
                        print("할인 적용 확인 완료!")
                        time.sleep(1)  # 확인 팝업이 뜰 시간을 잠시 줍니다.

                        page.click("button#confirmPopUpOk")
                        print("최종 확인 완료!")
                        result_message = "주차 1시간 할인이 적용되었습니다.!!!"
                        result_code = 200

                browser.close()
                return JsonResponse({"message": result_message, "resultCode": result_code },status=200)
            # resultCode :200 성공 ,100 문의 , 0 실패
        except Exception as e:
            return JsonResponse({"message": "자동화 처리 중 오류 발생", "resultCode":0}, status=500)

    return JsonResponse({"message": "POST 요청만 허용됩니다.", "resultCode": 0 }, status=405)