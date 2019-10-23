import jetsontx2.load_cameras as c
def main():
    data =[]
    data = c.load_cameras_from_file()
    print(f'test {data}')
    print(f'2: {data[0]}')
    
    #testReturn()
    

def testReturn():
     q1, q2, q3, q4 = multiReturn()
     print(f'{q1},{q2},{q3},{q4}')
     
def multiReturn():
    return 1,2,3,4



if __name__ == '__main__':
    main()
