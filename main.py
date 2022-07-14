# python3.10
from functions import get_web_page_selenium, skip_cloudflare
from functions import Settings
from functions import MySqlDataBase
import bs4
import os


def get_links(page: str, attribute: str, value: str) -> list[str]:
    bs_obj = bs4.BeautifulSoup(page, 'html.parser')
    links_obj = bs_obj.find_all(name='a', attrs={attribute: value})
    links: list[str] = []

    for link_obj in links_obj:
        link: str = link_obj.get('href')

        if link.find('javascript') == -1:
            if link.find('napaonline.com') == -1:
                links.append(f'https://www.napaonline.com{link}')
            else:
                links.append(link)

    return links


def get_finally_links(driver, links: list[str], attribute: str, value: str):
    finally_links: list[str] = []

    for link in links:
        category_page = get_web_page_selenium(driver, link)
        finally_links += get_links(category_page, attribute, value)

    return finally_links


def parse_products(driver, link: str):
    mysql_db = MySqlDataBase()
    mysql_db.DB_INFO = Settings.MYSQL_DB_INFO

    page = get_web_page_selenium(driver, link, 15)
    bs_obj = bs4.BeautifulSoup(page, 'html.parser')

    try:
        path_obj = bs_obj.find(name='ol', attrs={'class': 'geo-breadcrumb'})
        category_path = '/'.join(path_obj.findAll(text=True))
        cards_objs = bs_obj.find_all(name='div', attrs={'class': 'geo-productpod-middle'})
    except:
        return

    params: list[tuple] = []

    for card_obj in cards_objs:
        try:
            name: str = card_obj.find(name='div', attrs={'class': 'geo-pod-title geo-productpod-top'}).get('title')
            part_number: str = card_obj.find(name='div', attrs={'class': 'geo-pod-part'}).text.replace('Part #:', '')
            card_url: str = 'https://www.napaonline.com'
            card_url += card_obj.find(name='a', attrs={'class': 'geo-prod_pod_title'}).get('href')
            img_url: str = card_obj.find('img').get('src')
            price: str = card_obj.find(name='div', attrs={'class': 'geo-pod-price-cost'}).get('data-price')
        except:
            continue

        param = (
            category_path,
            name,
            part_number,
            card_url,
            img_url,
            price

        )

        params.append(param)

    query = """
               INSERT INTO parts_info (category_path, name, part_number, card_url, img_url, price)
               VALUES (%s, %s, %s, %s, %s, %s)
            """

    mysql_db.query_send_stack(query, params)


def save_links(name: str, links: list[str]):
    with open(name, 'w') as f:
        for link in links:
            f.write(f'{link}\n')


def read_links(name: str) -> list[str]:
    with open(name, 'r') as f:
        data = f.read().split('\n')

    return data


def parse_loop(driver, links):
    for link in links:
        finally_categories_links: list[str] = get_finally_links(driver, [link], 'class', 'geo-category-list-links')

        for fin_link in finally_categories_links:
            products_links: list[str] = get_finally_links(driver, [fin_link], 'class', 'geo-parttype-list-links')

            for product_link in products_links:
                parse_products(driver, product_link)


def main():
    driver = skip_cloudflare('https://www.napaonline.com/')
    main_page: str = get_web_page_selenium(driver, 'https://www.napaonline.com/')

    CURRENT_DIR: str = os.getcwd()

    if not os.path.exists(f'{CURRENT_DIR}/categories_links.txt'):
        categories_links: list[str] = get_links(main_page, 'class', 'geo-mega-menu-item')
        save_links('categories_links.txt', categories_links)
    else:
        categories_links: list[str] = read_links('categories_links.txt')

    if not os.path.exists(f'{CURRENT_DIR}/subcategories_links.txt'):
        subcategories_links: list[str] = get_finally_links(driver, categories_links, 'class', 'geo-category-list-links')
        save_links('subcategories_links.txt', subcategories_links)
    else:
        subcategories_links: list[str] = read_links('subcategories_links.txt')

    parse_loop(driver, subcategories_links)


if __name__ == "__main__":
    main()


