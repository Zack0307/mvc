# app.py
from flask import Flask, render_template, request, jsonify, session
import uuid

app = Flask(__name__)
app.secret_key = "secret_kiosk_key" # 用於加密 session

# --- 後端 Model: 模擬資料庫與狀態規則 ---
ORDER_STATES = {
    'NEW': 'NEW',               # 新訂單
    'IN_PROGRESS': 'IN_PROGRESS', # 點餐中
    'PENDING_PAY': 'PENDING_PAY', # 付款
    'PAID': 'PAID',             # 已付款
    'CANCELLED': 'CANCELLED'    # 已取消
}

class OrderManager:
    @staticmethod
    def get_order():
        return session.get('order', {
            'state': ORDER_STATES['NEW'],
            'items': [],
            'total': 0
        })

    @staticmethod
    def save_order(order):
        session['order'] = order

# --- 後端 Controller: 接收 Message 並驅動後端狀態機 ---
@app.route('/')
def index():
    # 進入首頁時初始化訂單
    session['order'] = {'state': ORDER_STATES['NEW'], 'items': [], 'total': 0}
    return render_template('index.html')

@app.route('/api/dispatch', methods=['POST'])
def dispatch():
    message = request.get_json()
    action = message.get('id')
    payload = message.get('payload')
    
    order = OrderManager.get_order()
    current_state = order['state']
    
    print(f"👮 後端收到 Message: {action}, 當前訂單狀態: {current_state}")

    # --- 後端狀態機轉移規則 (Business Logic) ---
    if action == 'ADD_ITEM':
        # 只有在「新訂單」或「點餐中」才允許加點
        if current_state in [ORDER_STATES['NEW'], ORDER_STATES['IN_PROGRESS']]:
            order['items'].append(payload)
            order['total'] += payload['price']
            order['state'] = ORDER_STATES['IN_PROGRESS']
            
    elif action == 'START_PAYMENT':
        if current_state == ORDER_STATES['IN_PROGRESS'] and len(order['items']) > 0:
            order['state'] = ORDER_STATES['PENDING_PAY']
            
    elif action == 'CONFIRM_PAY':
        if current_state == ORDER_STATES['PENDING_PAY']:
            order['state'] = ORDER_STATES['PAID']
            order['order_id'] = str(uuid.uuid4())[:8].upper() # 產生取餐碼
            
    elif action == 'SIMULATE_FAIL':
        # 模擬付款失敗
        order['state'] = ORDER_STATES['CANCELLED']

    OrderManager.save_order(order)
    
    # 將處理後的最新狀態回傳給前端 View
    return jsonify({
        'success': True,
        'backend_state': order['state'],
        'order_data': order
    })

if __name__ == '__main__':
    app.run(debug=True)