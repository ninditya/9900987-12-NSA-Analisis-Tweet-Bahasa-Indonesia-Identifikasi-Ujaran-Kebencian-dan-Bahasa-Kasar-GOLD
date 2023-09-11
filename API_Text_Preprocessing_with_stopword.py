# Gold Challenge
# 1. Terdapat API yang bisa menerima input user berupa teks dan file dengan 2 endpoint (10%)
# 2. Server API dibuat dengan Flask dan Swagger UI (25%) 
# 3. Penyimpanan data dalam SQLite menggunakan modul SQLite 3 (15%)
# 4. API yang bisa menghasilkan output berupa teks yang sudah di-cleansing (10%) 
# 5. API yang bisa memproses text cleansing (15%)

import re
import sqlite3
import pandas as pd

from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

app = Flask(__name__)
app.json_encoder = LazyJSONEncoder

#Swagger Template Interface
swagger_template = {
	"swagger":"2.0",
	"info":{
		"title": "API Documentation for Text Processing",
		"description": "Terdapat API yang bisa menerima input user berupa teks dan file dengan 2 endpoint. Server API dibuat dengan Flask dan Swagger UI. Penyimpanan data dalam SQLite menggunakan modul SQLite 3. API yang bisa menghasilkan output berupa teks yang sudah di-cleansing. API yang bisa memproses text cleansing.",
		"version": "1.0.0"
	}
}
swagger_config = {
	"headers" : [],
	"specs" : [
		{
			"endpoint" : 'docs',
			"route" : '/docs.json'
		}
	],
	"static_url_path" : '/flasgger_statis',
	"swagger_ui" : True,
	"specs_route" : "/docs/"
}
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# FUNGSI-FUNGSI TEXT CLEANSING #

# Mengubah Semua Huruf Menjadi Huruf Kecil
def lowercase(s):
    return s.lower()

# Hapus Semua Tanda Baca dan Kata yang Tidak Diperlukan
def punctuation(s):
    s = re.sub('[^0-9a-zA-Z]+', ' ', s) #menghilangkan semua karakter yang bukan huruf atau angka dan menggantinya dengan spasi.
    s = re.sub('^rt',' ', s) #menghapus awalan rt
    s = re.sub(r'\d+', '', s) #menghapus semua angka
    s = re.sub('user',' ', s) #menghapus kata 'user'
    s = re.sub(r':', ' ', s) #menggantikan karakter : dengan spasi
    s = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ', s) #menghapus semua URL 
    s = re.sub(' +', ' ', s) #menggantikan satu atau lebih spasi berturut-turut dengan satu spasi 
    s = re.sub('\n',' ',s) #menggantikan karakter newline (\n) dengan spasi 
    s = re.sub(r'pic.twitter.com.[\w]+', ' ', s) #menghapus semua tautan Twitter (pic.twitter.com)
    return s

# Load database kamusalay
db = sqlite3.connect('kamusalay_database.db', check_same_thread = False)
q_kamusalay = 'SELECT * FROM kamusalay'
t_kamusalay = pd.read_sql_query(q_kamusalay, db)
alay_dict = dict(zip(t_kamusalay['alay'], t_kamusalay['normal']))

# Normalisasi Kata Alay
def normalization(s):
    for word in alay_dict:
        return ' '.join([alay_dict[word] if word in alay_dict else word for word in s.split(' ')])

# Load data abusive
db = sqlite3.connect('abusive_database.db', check_same_thread=False)
q_abusive = 'SELECT * FROM abusive'
t_abusive = pd.read_sql_query(q_abusive, db)

# Fungsi Removal Kata Abusive
def abusive_removal(s):
    abusive_words = set(t_abusive['ABUSIVE'])
    words = s.split()
    filtered_words = [word for word in words if word not in abusive_words]
    return ' '.join(filtered_words)

# Load data stopwords
db = sqlite3.connect('stopword_database.db', check_same_thread=False)
q_stopword = 'SELECT * FROM stopword'
t_stopword = pd.read_sql_query(q_stopword, db)

# Fungsi Removal Stopword
def stopword_removal(s):
    stopword_words = set(t_stopword['STOPWORD'])
    words = s.split()
    filtered_words = [word for word in words if word not in stopword_words]
    return ' '.join(filtered_words)
    
# Fungsi Text Cleansing
def text_cleansing(s):
    s = lowercase(s)
    s = punctuation(s)
    s = abusive_removal(s)
    s = normalization(s)
    s = stopword_removal(s)
    return s

# Endpoint Home Page
@swag_from("docs/HomePage.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "API yang bisa menghasilkan output berupa teks yang sudah di-cleansing, inputan dapat berupa text dan file",
        'data': "DSC 12 - API Text Processing by Ninditya Salma Nur Aini",
    }
    response_data = jsonify(json_response)
    return response_data

# Endpoint Text Processing
@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    text = request.form.get('text')

    # Memanggil fungsi text_cleansing
    cleaned_text = text_cleansing(text)

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_text,
    }
    response_data = jsonify(json_response)
    return response_data

# Endpoint Text Processing File
@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():

    # Upladed file
    file = request.files.getlist('file')[0]

    # Import file csv ke Pandas
    df = pd.read_csv(file, encoding='latin-1')

    # Lakukan cleansing pada teks
    cleaned_text = []
    for text in df['Tweet']:
        cleaned_text.append(text_cleansing(text))
    df['cleaned_text'] = cleaned_text

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_text
    }

    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
   app.run()