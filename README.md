# كاشف النصب

نسختين من نفس المشروع:
- **سحابية (Streamlit Cloud):** لينك دايم، RAG خفيف + Groq API. ملف requirements.txt
- **Kaggle (GPU):** الموديل المتدرب QLoRA + ngrok. ملف requirements-kaggle.txt

## نشر النسخة السحابية
1. ارفع كل الملفات على GitHub (ريبو Public).
2. اعمل مفتاح مجاني من console.groq.com
3. روح share.streamlit.io > New app > اختار الريبو، Branch = main، Main file = app.py
4. Advanced settings > Secrets، والصق:
   GROQ_API_KEY = "مفتاحك"
5. Deploy، وبعد دقيقتين تاخد لينك زي https://اسم-التطبيق.streamlit.app

## Kaggle
افتح kaggle_notebook.ipynb (GPU T4 + Internet On + Secret باسم NGROK_TOKEN).
