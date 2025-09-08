
HTML = str

def tablize(ll:list[list],titles:list[str]=[]) -> HTML:
    """ Transform list of list in html/table """
    if ll:
        h=["<table border=1 cellspacing=0 cellpadding=2 style='font-size:0.8em'>"]
        if titles:
            h.append("<tr>%s</tr>" % "".join( [f"<th>{i}</th>" for i in titles]))
        for row in ll:
            h.append("<tr>")
            if isinstance(row,dict):
                for item in row.items():
                    h.append(f"<td>{item}</td>")
            else:
                for item in row:
                    h.append(f"<td>{item}</td>")
            h.append("</tr>")
        h.append("</table>")
        return "".join(h)
    else:
        return ""


if __name__=="__main__":
    ...
    # ll=[ (1,2,3), (11,22,32)]
    # h=tablize(ll)
    # print(h)