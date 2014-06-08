import evelink.char # Wrapped API access for the /char/ API path
import time         # for time.time()

eve = evelink.eve.EVE()
api = evelink.api.API(api_key=(1288525, 'xUHKT2V7j0lsIlSWq7D8MQrxelPiNFad2MS6fa5xJrbeC8haJ1HpVmRLk73IAO8g'))
id_response = eve.character_id_from_name("Emerald Placide")
char = evelink.char.Char(char_id = id_response.result, api=api)
print("Getting balance...")
balance_response = char.wallet_balance()
print(balance_response.result)

#some time markers that will be handy when reading market transactions
time_today = time.time()
#60 seconds * 60 minutes * 24 hours * 7 days
time_week = time_today - (60*60*24*7)
#60 seconds * 60 minutes * 24 hours * 30 days
time_month = time_today - (60*60*24*30)

inventory = {}
station_map = {}

class inventory_item(object):
    def __init__(self, type_id):
        self.type_id = type_id
        self.type_name = None
        self.stats_current = True
        self.sales = []
        self.purchases = []
        self.orders = []
        self.month_sales = 0
        self.month_revenue = 0
        self.month_sellrate = 0
        self.week_sales = 0
        self.week_revenue = 0
        self.week_sellrate = 0
        self.month_purchases = 0
        self.month_expenses = 0
        self.week_purchases = 0
        self.week_expenses = 0
        self.total_on_sale = 0
        self.on_sale = {}
        self.inventory = {}
    def __repr__(self):
        if self.type_name:
            return self.type_name
        else:
            return "ItemID " + str(self.type_id)
    def add_transaction(self, trans):
        self.stats_current = False
        if trans['action'] == 'buy':
            self.purchases.append(trans)
        elif trans['action'] == 'sell':
            self.sales.append(trans)
        if not self.type_name:
            self.type_name = trans['type']['name']
    def add_order(self, order):
        self.stats_current = False
        self.orders.append(order)
    def update_sale_stats(self):
        self.month_sales = 0
        self.month_revenue = 0
        self.week_sales = 0
        self.week_revenue = 0
        for sale in self.sales:
            sale_qty = sale['quantity']
            sale_val = sale['price'] * sale_qty
            if sale['timestamp'] > time_month:
                self.month_sales = self.month_sales + sale_qty
                self.month_revenue = self.month_revenue + sale_val
            if sale['timestamp'] > time_week:
                self.week_sales = self.week_sales + sale_qty
                self.week_revenue = self.week_revenue + sale_val
        self.month_sellrate = self.month_sales / 30.0
        self.week_sellrate = self.week_sales / 30.0
    def update_purchase_stats(self):
        self.month_purchases = 0
        self.month_expenses = 0
        self.week_purchases = 0
        self.week_expenses = 0
        for purchase in self.purchases:
            buy_qty = purchase['quantity']
            buy_val = purchase['price'] * buy_qty
            if purchase['timestamp'] > time_month:
                self.month_purchases = self.month_purchases + buy_qty
                self.month_expenses = self.month_expenses + buy_val
            if purchase['timestamp'] > time_week:
                self.week_purchases = self.week_purchases + buy_qty
                self.week_expenses = self.week_expenses + buy_val
    def update_inventory_stats(self):
        self.on_sale = {}
        self.total_on_sale = 0
        for order in self.orders:
            if order['amount_left'] != 0:
                if order['station_id'] not in self.on_sale:
                    self.on_sale[order['station_id']] = 0
                self.on_sale[order['station_id']] = self.on_sale[order['station_id']] + order['amount_left']
                self.total_on_sale = self.total_on_sale + order['amount_left']
    def calculate_stats(self):
        self.update_sale_stats()
        self.update_purchase_stats()
        self.update_inventory_stats()
        self.stats_current = True
    def print_general_stats(self):
        if not self.stats_current:
            self.calculate_stats()
        print("Item", self.type_id, ":" , (self.type_name or "Unnamed Item"))
        for station in self.on_sale:
            print(self.on_sale[station], "items on sale in", station_map[station])
        print("Sold", self.month_sales, "items in the past month")
        print(" and", self.week_sales, "items in the past week.")
        print("That is", self.month_sellrate, "per day.")
        print("Estimated time to exhaustion is", self.time_to_exhaustion())
        print("Revenue from this item was", (self.month_revenue / 1000000), "million ISK this month.")
        print("Estimated profit is", (self.est_profit() / 1000000), "million ISK this month\n")
    #TODO do this better
    def time_to_exhaustion(self):
        if not self.stats_current:
            self.calculate_stats()
        duration_month = 1000
        duration_week = 1000
        if self.month_sales > 0:
            duration_month = (30.0 * self.total_on_sale) / self.month_sales
        if self.week_sales > 0:
            duration_week = (7.0 * self.total_on_sale) / self.week_sales
        return min(duration_month, duration_week)
    def est_profit(self):
        if self.month_purchases and self.month_sales:
            est_cost_basis = self.month_expenses / self.month_purchases
            avg_sale_price = self.month_revenue / self.month_sales
            return (avg_sale_price - est_cost_basis) * self.month_sales
        else:
            return self.month_revenue

def get_transactions():
    #refresh time
    time_today = time.time()
    #60 seconds * 60 minutes * 24 hours * 7 days
    time_week = time_today - (60*60*24*7)
    #60 seconds * 60 minutes * 24 hours * 30 days
    time_month = time_today - (60*60*24*30)
    oldest_trans_time = time_today
    oldest_trans_id = 0

    transactions, current, expires = char.wallet_transactions(limit=2560)
    while transactions:
        for trans in transactions:
            if trans['timestamp'] < oldest_trans_time:
                oldest_trans_time = trans['timestamp']
                oldest_trans_id = trans['id']
                if trans['type']['id'] not in inventory:
                    inventory[trans['type']['id']] = inventory_item(trans['type']['id'])
                inventory[trans['type']['id']].add_transaction(trans)
                if trans['station']['id'] not in station_map:
                    station_map[trans['station']['id']] = trans['station']['name']
        print("Oldest transaction processed is " + time.asctime(time.gmtime(oldest_trans_time)))
        print("Walking to older transactions.")
        transactions, current, expires = char.wallet_transactions(before_id = oldest_trans_id, limit=2560)

def get_orders():
    orders, current, expires = char.orders()
    for order_id in orders:
        order = orders[order_id]
        order_type = order['type_id']
        if order_type not in inventory:
            inventory[order_type] = inventory_item(order_type)
        inventory[order_type].add_order(order)

def print_urgent_orders():
    filtered_items = filter(lambda item: (item.time_to_exhaustion() < 2), inventory.values())
    for item in sorted(filtered_items, key=lambda item: item.est_profit()):
        item.print_general_stats()

get_transactions()
get_orders()
print("---------------------")
print_urgent_orders()
