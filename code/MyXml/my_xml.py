#coding = utf-8
"""
xml操作xml文件
"""

import xml.dom.minidom


class MyXml(object):
    """
    xml类
    """
    @staticmethod
    def get_tag_attributes() -> None:
        """
        获取标签属性
        """
        dom = xml.dom.minidom.parse("test.xml")  # 打开xml文档

        root = dom.documentElement  # 得到xml文档对象
        print("nodeName: <%s>" % root.nodeName)  # 每一个结点都有它的nodeName，nodeValue，nodeType属性
        print("nodeValue:", root.nodeValue)  # nodeValue是结点的值，只对文本结点有效
        print("nodeType:", root.nodeType)
        print("ELEMENT_NODE:", root.ELEMENT_NODE)

        # 获得子标签
        dd = root.getElementsByTagName('maxid')
        b = dd[0]
        print("type(dd): %s, dd: %s, b.nodeName: %s, b.nodeValue: %s" % (type(dd), dd, b.nodeName, b.nodeValue))

        # 获得标签属性组织
        itemlist = root.getElementsByTagName('login')
        item = itemlist[0]
        print(item.getAttribute("username"))
        print(item.getAttribute("passwd"))


        itemlist = root.getElementsByTagName("item")
        item = itemlist[0]  # 通过在itemlist中的位置区分
        print(item.getAttribute("id"))

        item2 = itemlist[1]  # 通过在itemlist中的位置区分
        print(item2.getAttribute("id"))

        # 获得标签对之间的数据
        itemlist = root.getElementsByTagName('caption')

        item = itemlist[0]
        print(item.firstChild.data)

        item2 = itemlist[1]
        print(item2.firstChild.data)

        for node in root.childNodes:
            print(node.nodeName)

    @staticmethod
    def set_xml_file() -> None:
        """
        生成xml文件
        """
        # 1.创建DOM树对象
        dom = xml.dom.minidom.Document()
        # 2.创建根节点。每次都要用DOM对象来创建任何节点。
        root_node = dom.createElement('root')
        # 3.用DOM对象添加根节点
        dom.appendChild(root_node)

        # 用DOM对象创建元素子节点
        book_node = dom.createElement('book')
        # 用父节点对象添加元素子节点
        root_node.appendChild(book_node)
        # 设置该节点的属性
        book_node.setAttribute('price', '199')

        name_node = dom.createElement('name')
        root_node.appendChild(name_node)
        # 也用DOM创建文本节点，把文本节点（文字内容）看成子节点
        name_text = dom.createTextNode('hello world')
        # 用添加了文本的节点对象（看成文本节点的父节点）添加文本节点
        name_node.appendChild(name_text)

        # 每一个结点对象（包括dom对象本身）都有输出XML内容的方法，如：toxml()--字符串, toprettyxml()--美化树形格式。

        try:
            with open('dom_write.xml', 'w', encoding='UTF-8') as fh:
                # 4.writexml()第一个参数是目标文件对象，第二个参数是根节点的缩进格式，第三个参数是其他子节点的缩进格式，
                # 第四个参数制定了换行格式，第五个参数制定了xml内容的编码。
                dom.writexml(fh, indent='', addindent='\t', newl='\n', encoding='UTF-8')
                print('写入xml OK!')
        except Exception as err:
            print('错误信息：{0}'.format(err))


if __name__ == '__main__':
    my_xml = MyXml()
    my_xml.get_tag_attributes()
    my_xml.set_xml_file()