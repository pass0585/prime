# score_editor.py
import streamlit as st
import pandas as pd
import io

try:
    import firebase_admin
    from firebase_admin import firestore
except ModuleNotFoundError as e:
    st.error("Firebase 관련 모듈이 누락되었습니다. 실행 환경을 확인해주세요.")
    st.stop()

# Firebase DB 연결
if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

def get_user_list():
    try:
        users_ref = db.collection("users").stream()
        user_list = []
        for user in users_ref:
            info = user.to_dict()
            user_list.append(info.get("이름", user.id))
        return sorted(user_list)
    except Exception as e:
        st.error("사용자 목록을 불러오지 못했습니다: " + str(e))
        return []

def get_class_list():
    try:
        classes_ref = db.collection("students")
        docs = classes_ref.stream()
        반_set = set()
        for doc in docs:
            반 = doc.to_dict().get("반")
            if 반:
                반_set.add(반)
        return sorted(list(반_set))
    except Exception as e:
        st.error("반 목록을 불러오지 못했습니다: " + str(e))
        return []

def get_students_by_class(반이름):
    try:
        students_ref = db.collection("students")
        query = students_ref.where("반", "==", 반이름).stream()
        students = []
        for doc in query:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            students.append(data)
        return students
    except Exception as e:
        st.error("학생 목록을 불러오지 못했습니다: " + str(e))
        return []

def upload_excel_to_firestore(file):
    try:
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            data = row.dropna().to_dict()
            if "학번" in data:
                doc_id = str(data["학번"])
                db.collection("students").document(doc_id).set(data)
    except Exception as e:
        st.error("엑셀 업로드 중 오류 발생: " + str(e))

def 점수입력화면():
    사용자목록 = get_user_list()
    if 사용자목록:
        선택사용자 = st.selectbox("사용자를 선택하세요:", 사용자목록)
        st.markdown(f"**현재 사용자:** {선택사용자}")

    # 🔽 엑셀 업로드 기능
    with st.expander("📥 엑셀로 학생 정보 업로드"):
        uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx"])
        if uploaded_file:
            upload_excel_to_firestore(uploaded_file)
            st.success("✅ 학생 데이터가 Firebase에 업로드되었습니다.")

    반_목록 = get_class_list()
    if 반_목록:
        선택_반 = st.selectbox("반을 선택하세요:", 반_목록)
        학생목록 = get_students_by_class(선택_반)

        st.subheader(f"{선택_반} 학생 목록")
        점수수정 = {}
        for student in 학생목록:
            score = st.number_input(
                f"{student['이름']} ({student['학번']}) 수학 점수:",
                min_value=0, max_value=100,
                value=int(student.get("수학점수", 0)) if student.get("수학점수") else 0,
                key=student["doc_id"]
            )
            점수수정[student["doc_id"]] = score

        if st.button("저장"):
            for doc_id, new_score in 점수수정.items():
                db.collection("students").document(doc_id).update({"수학점수": new_score})
            st.success("✅ Firebase에 점수가 저장되었습니다.")

# main.py
import streamlit as st
from score_editor import 점수입력화면

st.set_page_config(page_title="학원 수학 점수 관리", layout="wide")
st.title("📘 학원 수학 점수 관리 (Firebase 연결)")

점수입력화면()
