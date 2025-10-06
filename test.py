# from gettext import find
# import re
# from tracemalloc import start
# # /(color|background-color)\s*:\s*(#[0-9a-fA-F]+|\w+|rgb\([^)]+\))/

# def check_is_ok(color):
#     color = color[1:].lower()
#     chars = "0123456789abcdef"
#     flag = all(num in chars for num in color)
#     return flag


# def css_extractor(css_code):
#     colors = []
#     pos = 0
#     while True:

#         ind_resh = css_code.find("#", pos)
#         if ind_resh == -1:
#             break
#         if css_code[ind_resh + 4] == ";":
#             colors.append(css_code[ind_resh:ind_resh + 4])
#             pos += ind_resh + 4
#         elif css_code[ind_resh + 7] == ";":
#             colors.append(css_code[ind_resh:ind_resh + 7])
#             pos += ind_resh + 7
        
#     for color in colors:
#         if check_is_ok(color):
#             print(color)
   
    

# # Чтение входных данных
# # n = int(input())
# css_code = '''body {
#   color: #FFF;
#   background-color: #121212;
# }'''

# css_extractor(css_code)




# def transpose_matrix(matrix):
#     n = len(matrix)
#     m = len(matrix[0])
#     new = [[0 for j in range(n)] for i in range(m)]
#     for i in range(n):
#         for j in range(m):
#             new[j][i] = matrix[i][j]
#     return new

# n, m = map(int, input().strip().split())
# matrix = []
# for _ in range(n):
#     row = list(map(int, input().strip().split()))
#     matrix.append(row)

# result = transpose_matrix(matrix)

# for row in result:
#     print(' '.join(map(str, row)))


# def min_amplitude(arr):
#     sort_arr = sorted(arr)
#     dif = []
#     for i in range(len(sort_arr) - 1):
#         dif.append(abs(sort_arr[i] - sort_arr[i+1]))
        
#     print(dif)
#     print(sort_arr)
    
#     sort_dif = sorted(dif, reverse=True)[:3]
    
#     for el in sort_dif:
#         need_to_change = 
#         while True:
#             start = dif.index(el)
#             try:
#                 if dif[start + 1] in sort_dif:
#                     continue

#             except:
#                 print("error")
#             break
            
        
#     return True
        

# # Чтение входных данных
# arr = [-8, -1,3,4,5,7,10]
# result = min_amplitude(arr)
# print(result)

ans = [
	{ "n": "9", "m": 2, "expected": 0 },
	{ "n": "10", "m": 2, "expected": 1 },
	{ "n": "1025", "m": 55, "expected": 5 },
	{ "n": "12589", "m": 369, "expected": 89 },
	{ "n": "1598753", "m": 25897, "expected": 20305 },
	{ "n": "60282445765134413", "m": 2263, "expected": 974 }
]

def fib_mod(n, m):
    fib = [0, 1]
    mod = [0, 1 % m]
    for i in range(2, 30):
        fib.append(fib[i-1] + fib[i-2])
        mod.append((fib[i-1] + fib[i-2])%m)
    return mod

def main():
    n, m = map(int, input().split())
    print(fib_mod(n, m))


if __name__ == "__main__":
    main()