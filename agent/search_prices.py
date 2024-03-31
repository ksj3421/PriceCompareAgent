import requests
import json 
import copy
import pandas as pd
from bs4 import BeautifulSoup

# Define the headers to simulate a browser visit
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582'
}

def get_price_compare(max_page):
    # Find all script tags
    final_list = []
    final_back_data = pd.DataFrame()
    for PageIndex in range(0, max_page):
        category_url = get_category_url(PageIndex)
        response = requests.get(category_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the <script> tag with id="__NEXT_DATA__"
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        # Extract the JSON string from the script tag
        json_string = script_tag.string if script_tag else ''

        # Parse the JSON string into a Python dictionary
        data = json.loads(json_string) if json_string else {}

        for item in data['props']['pageProps']['initialState']["products"]["list"]:
            coupang_price = 0
            if ("lowMallList" in item['item']) and (item['item']["lowMallList"] is not None):
                df = copy.deepcopy(pd.DataFrame(item['item']["lowMallList"]))
                product_info = copy.deepcopy(pd.DataFrame(item['item']["purchaseConditionInfos"]))
                df['productTitle'] = item['item']["productTitle"]
                df['lowPrice'] = item['item']["lowPrice"]
                df['priceUnit'] = item['item']["priceUnit"]
                df['reviewCount'] = item['item']["reviewCount"]
                coupang_price = None
                row_price = None
                if df.name.apply(lambda x: '쿠팡' in x).sum() > 0:
                    for i, row in df.iterrows():
                        if (i == 0) & ('쿠팡' in row['name']) & ('모모상점' in row['name']):
                            continue  # Skip to the next item
                        elif (i == 0) & ('쿠팡' not in row['name']) & ('모모상점' not in row['name']):
                            row_price = row['lowPrice']
                            row_seller = row['name']
                        elif '쿠팡' in row['name']:
                            coupang_price = row['price']
                if (coupang_price is not None) & (row_price is not None):
                    if (((int(coupang_price) / row_price) > 1.3) and ((int(coupang_price) / row_price) < 1.8)):
                        final_url = get_category_url(PageIndex)
                        final_dict = {"물품명": row['productTitle'], "판매사": row_seller, "최저가": row_price, "쿠팡가격": coupang_price, "비율": int(coupang_price) / row_price, "page": final_url, "detailPage": product_info.iloc[0]['crUrl']}
                        print(final_dict)
                        final_list.append(final_dict)
                        bf_final_df = pd.concat([df, pd.DataFrame([final_dict]*df.shape[0])], axis=1)
                        final_back_data = pd.concat([final_back_data, bf_final_df], axis=0)
    return final_list, final_back_data

# TO DO: Implement the function to get the category URL
def get_category_url(page_index):
    return f"https://search.shopping.naver.com/search/category/100000947?adQuery&catId=50000455&origQuery&pagingIndex={str(page_index)}&pagingSize=40&productSet=total&query&sort=review&timestamp=&viewType=list"

if __name__ == "__main__":
    max_page = 20
    final_list, final_back_data = get_price_compare(max_page)
    res = pd.DataFrame(final_list)
    res.to_csv("final_csv.csv", encoding='utf-8-sig', index=False)
    final_back_data.to_csv("final_back_data.csv", encoding='utf-8-sig', index=False)
    