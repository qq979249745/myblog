# -*- coding: utf-8 -*-
import datetime
import requests
from bs4 import BeautifulSoup
import html2text as ht
import re
import pymysql
import random


def getHtml(url, tag, attrs):
    req = requests.get(url)
    req.encoding = req.apparent_encoding
    text = req.text
    bs = BeautifulSoup(text, 'html.parser')
    tag = bs.findAll(tag, attrs)
    return tag


def html2md(html):
    text_maker = ht.HTML2Text()
    text_maker.images_as_html = True
    text = text_maker.handle(html)
    text = re.compile(r'(\s{4})\d+\s').sub(r'\1', text)  # 去除代码片段的行号
    text = re.compile(r'\[(.*?)\]\(.*?://.*?\)').sub(r'\1', text)  # 去除标题的链接
    text = re.compile(r'posted ([\s\S]*)').sub('', text)  # 去除尾部
    text = re.compile(r"<img.*?src='(.*?)'.*?/>", re.S).sub(r'![图片](\1)', text)  # 转换成md形式的图片
    return text


def getAllArticle(url):
    html = getHtml(url, 'a', {'class': 'entrylistItemTitle'})
    return html


def getConnect():
    db = pymysql.connect(host='47.101.148.156', user='user', password='password', port=3306,
                         database='my_blog_db')
    return db


def insertBlog(blog_title, blog_content, blog_tags):
    img = "/admin/dist/img/rand/{index}.jpg".format(index=random.randint(1, 40))
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into tb_blog values(null,'%s','','%s','%s',24,'技术文章','%s',1,0,0,0,'%s','%s');" % (
        pymysql.escape_string(blog_title), img, pymysql.escape_string(blog_content), blog_tags, update_time,
        update_time)
    return sql


def selectTitle(title):
    sql = "select count(*) from tb_blog where blog_title='%s';" % (pymysql.escape_string(title))
    return sql


def insertTag(tag, cursor):
    sql = "select count(*) from tb_blog_tag where tag_name='%s';" % (pymysql.escape_string(tag))
    cursor.execute(sql)
    if cursor.fetchone()[0] == 0:
        print('没有%s这个标签，插入此标签' % (tag))
        sql = "insert into tb_blog_tag values(null, '%s',0,'%s');" % (
            pymysql.escape_string(tag), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute(sql)


def main():
    tag = 'Hadoop'  # 填写博客的标签
    db = getConnect()
    cursor = db.cursor()
    insertTag(tag, cursor)
    html = getAllArticle('https://www.cnblogs.com/sunddenly/category/611923.html')  # 链接要填写博客园中是分类的，从而爬取这个分类下所有博客
    for i in html:
        print(i['href'], i.text)
        sql = selectTitle(i.text)  # 查询有没有这篇博客
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        if count != 0:
            print(count, i.text, '博客已存在')
        else:
            print(i.text, '没有这篇博客')
            html = getHtml(i['href'], 'div', {'id': 'post_detail'})
            if html[0]:
                md = html2md(html[0].encode('gbk').decode('gbk'))
                sql = insertBlog(i.text, md, tag)
                print(cursor.execute(sql), '1为插入成功')
                db.commit()

    cursor.close()
    db.close()


if __name__ == '__main__':
    main()
