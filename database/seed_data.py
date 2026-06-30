from database import get_db_connection

def insert_sample_data():
    conn = get_db_connection()
    
    tags = [
        ('亲子', '#52c41a'),
        ('摄影', '#722ed1'),
        ('人文', '#fa8c16'),
        ('海边', '#1890ff'),
        ('美食', '#eb2f96'),
        ('低强度', '#13c2c2'),
        ('历史', '#faad14'),
        ('自然风光', '#52c41a'),
        ('购物', '#2f54eb'),
    ]
    
    for name, color in tags:
        conn.execute('INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)', (name, color))
    
    attractions = [
        {
            'name': '鼓浪屿',
            'description': '鼓浪屿是厦门最具代表性的景点，被誉为"海上花园"。这里有众多的欧式建筑、美丽的海滩和丰富的文化遗产。岛上禁止机动车通行，只能步行或乘坐电瓶车，是一个非常适合慢游的地方。',
            'image_url': '/static/images/gulangyu.jpg',
            'address': '厦门市思明区鼓浪屿',
            'open_time': '全天开放',
            'recommended_duration': 360,
            'rating': 4.8,
            'popularity': 98,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4446,
            'longitude': 118.0666
        },
        {
            'name': '厦门大学',
            'description': '厦门大学是中国最美的大学之一，校园内有芙蓉湖、情人谷等美景，建筑风格中西合璧。背靠五老峰，面朝大海，环境优美，是游客必打卡的地方。',
            'image_url': '/static/images/xiamen_university.jpg',
            'address': '厦门市思明区思明南路422号',
            'open_time': '周一至周五 12:00-14:00, 17:00后；周末全天',
            'recommended_duration': 180,
            'rating': 4.7,
            'popularity': 95,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4346,
            'longitude': 118.0819
        },
        {
            'name': '环岛路',
            'description': '厦门环岛路是一条美丽的海滨公路，全长43公里。沿途风景优美，可以骑行、散步或驾车欣赏海景。其中白城沙滩、黄厝海滩等都是著名的景点。',
            'image_url': '/static/images/huan_dao_road.jpg',
            'address': '厦门市思明区环岛路',
            'open_time': '全天开放',
            'recommended_duration': 240,
            'rating': 4.6,
            'popularity': 90,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4423,
            'longitude': 118.1066
        },
        {
            'name': '南普陀寺',
            'description': '南普陀寺是闽南著名的佛教寺院，始建于唐代。寺内有天王殿、大雄宝殿、藏经阁等建筑，后山五老峰风景秀丽，可俯瞰厦门市区和大海。',
            'image_url': '/static/images/nanputuo_temple.jpg',
            'address': '厦门市思明区思明南路515号',
            'open_time': '8:00-17:30',
            'recommended_duration': 120,
            'rating': 4.5,
            'popularity': 85,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4396,
            'longitude': 118.0789
        },
        {
            'name': '曾厝垵',
            'description': '曾厝垵是一个充满文艺气息的渔村，现在已经发展成为厦门最热闹的夜市之一。这里有各种美食小吃、特色小店和民宿，是年轻人喜欢聚集的地方。',
            'image_url': '/static/images/zengcuoan.jpg',
            'address': '厦门市思明区曾厝垵',
            'open_time': '全天开放',
            'recommended_duration': 180,
            'rating': 4.4,
            'popularity': 88,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4646,
            'longitude': 118.1166
        },
        {
            'name': '沙坡尾',
            'description': '沙坡尾是厦门港的发源地，曾经是渔船停泊的避风坞。如今这里已经改造成为一个文艺创意园区，有各种咖啡馆、艺术工作室和特色餐厅。',
            'image_url': '/static/images/shapowei.jpg',
            'address': '厦门市思明区沙坡尾',
            'open_time': '全天开放',
            'recommended_duration': 150,
            'rating': 4.3,
            'popularity': 82,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4316,
            'longitude': 118.0689
        },
        {
            'name': '中山路',
            'description': '中山路是厦门最繁华的商业街，始建于1925年，是厦门历史最悠久的街道之一。这里汇集了众多老字号店铺、特色小吃和现代商场，是购物和品尝美食的好去处。',
            'image_url': '/static/images/zhongshan_road.jpg',
            'address': '厦门市思明区中山路',
            'open_time': '全天开放',
            'recommended_duration': 180,
            'rating': 4.5,
            'popularity': 92,
            'area': '思明区',
            'price': 0,
            'latitude': 24.4416,
            'longitude': 118.0716
        },
    ]
    
    for attr in attractions:
        conn.execute('''
            INSERT INTO attractions (name, description, image_url, address, 
                                    open_time, recommended_duration, rating, 
                                    popularity, area, price, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attr['name'], attr['description'], attr['image_url'], attr['address'],
            attr['open_time'], attr['recommended_duration'], attr['rating'],
            attr['popularity'], attr['area'], attr['price'], attr['latitude'], attr['longitude']
        ))
    
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (1, 2), (1, 3), (1, 4), (1, 7)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (2, 2), (2, 3), (2, 8)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (3, 1), (3, 2), (3, 4), (3, 6), (3, 8)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (4, 3), (4, 7), (4, 8)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (5, 1), (5, 5), (5, 4)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (6, 2), (6, 5), (6, 8)')
    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (7, 3), (7, 5), (7, 7), (7, 9)')
    
    comments = [
        (1, '张三', '鼓浪屿真的太美了，一定要住一晚！', 5),
        (1, '李四', '岛上的建筑很有特色，适合拍照。', 4),
        (2, '王五', '厦大的芙蓉隧道很有意思，涂鸦很有创意。', 5),
        (3, '赵六', '环岛路骑行非常舒服，风景一流。', 5),
        (4, '孙七', '南普陀寺很安静，香火很旺。', 4),
    ]
    
    for attraction_id, username, content, rating in comments:
        conn.execute('INSERT INTO comments (attraction_id, username, content, rating) VALUES (?, ?, ?, ?)',
                     (attraction_id, username, content, rating))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    insert_sample_data()
    print('Sample data inserted successfully!')
