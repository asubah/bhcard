from bhcard import BhCard

card_data = BhCard.getData()
print(card_data['cpr'])
print(card_data['full_name'])
print(card_data['issue_date'])
print(card_data['expiry_date'])
print(card_data['workplace'])
        

