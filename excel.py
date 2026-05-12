import pandas as pd
import re   
import threading

excel_write_lock = threading.Lock()

def  stt_Acc(name_profile):
    match = re.search(r'ACC \((\d+)\)', name_profile)
    if not match:
        return False
    return int(match.group(1))

#Xử lý execl
def read_excel_file(filepath, sheet_name=None):
    """
    Đọc file Excel và trả về dữ liệu dạng list các tuple (row_index, row_data).
    - filepath: đường dẫn file excel
    - sheet_name: tên sheet muốn đọc (nếu None sẽ lấy sheet đầu tiên)
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        data = df.values.tolist()
        # Trả về list các tuple (row_index, row_data)
        data_with_index = [(idx+1, row) for idx, row in enumerate(data)]
        return data_with_index
    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")
        return None
def extract_first_integer(s):
    """
    Trả về dãy số nguyên đầu tiên trong chuỗi s (không bắt đầu bằng 0, trừ khi là '0').
    Nếu không tìm thấy, trả về None.
    """
    s=str(s)
    i = 0
    n = len(s)
    while i < n:
        if s[i].isdigit():
            # Nếu là số 0 đứng đầu và phía sau còn số, bỏ qua
            if s[i] == '0' and i+1 < n and s[i+1].isdigit():
                i += 1
                continue
            start = i
            while i < n and s[i].isdigit():
                i += 1
            return int(s[start:i])
        i += 1
    return None


    


def process_excel_data(filepath, sheet_name=None):
    """
    Đọc file Excel và trả về list các tuple (row_index, num) với điều kiện cột Z là None.
    - filepath: đường dẫn file excel
    - sheet_name: tên sheet muốn đọc (nếu None sẽ lấy sheet đầu tiên)
    """
    profile_notOk = []
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        # Nếu df là dict (nhiều sheet), lấy sheet đầu tiên
        if isinstance(df, dict):
            first_sheet = list(df.keys())[0]
            df = df[first_sheet]
        for idx, row in enumerate(df.values.tolist()):
            if len(row) > 25:
                col_a = str(row[0]) if row[0] is not None else ""
                col_z = row[25]
                if pd.isna(col_z):
                    num = extract_first_integer(col_a)
                    if num is not None:
                        profile_notOk.append((idx, num))
    except Exception as e:
        print(f"Lỗi khi xử lý file Excel: {e}")
    return profile_notOk

# Ví dụ sử dụng:
# result = process_excel_data('duongdan.xlsx')
# print(result)

def write_error_to_file(path_file_error, sheet_name, profile_name, text_error):
    """
    Ghi dữ liệu lỗi vào sheet cụ thể trong file Excel.
    - Xóa hết dữ liệu cũ trong sheet đó trước khi ghi mới.
    - Cột A: profile_name, Cột B: text_error.
    """

    df = pd.DataFrame([[profile_name, text_error]])

    try:
        # Nếu file đã tồn tại, chỉ ghi đè sheet cần thiết, giữ nguyên các sheet khác
        with pd.ExcelWriter(path_file_error, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)
    except FileNotFoundError:
        # Nếu file chưa tồn tại, tạo mới
        with pd.ExcelWriter(path_file_error, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# write_error_to_file('Error_GPM - Copy.xlsx', 'Error', 'acc5', 'Không thể đăng nhập. Đang thử lại...')

def update_column_z_ok(path_data_excel, id_row):
    try:
        df = pd.read_excel(path_data_excel)
        # Ép kiểu cột Z sang string để tránh cảnh báo
        df.iloc[:, 25] = df.iloc[:, 25].astype(str)
        df.iloc[id_row, 25] = "OK"
        df.to_excel(path_data_excel, index=False)
        print(f"Đã cập nhật dòng {id_row+1} cột Z thành 'OK' trong file {path_data_excel}")
    except Exception as e:
        print(f"Lỗi khi cập nhật file Excel: {e}")

def write_bot_running_details(data, columns, file_path="Bot_Running_Details.xlsx"):
    """
    Ghi dữ liệu trạng thái bot vào file Excel Bot_Running_Details.xlsx.
    - data: list các list/tuple, mỗi phần tử là 1 dòng dữ liệu.
    - columns: list tên cột.
    - file_path: đường dẫn file Excel (mặc định là Bot_Running_Details.xlsx)
    Nếu file đã tồn tại sẽ xóa hết và ghi lại, nếu chưa có sẽ tạo mới.
    """
    df = pd.DataFrame(data, columns=columns)
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)
    except Exception as e:
        print(f"Lỗi khi ghi file trạng thái bot: {e}")

def load_status_grid_from_excel(file_path="Bot_Running_Details.xlsx"):
    """
    Đọc dữ liệu từ file Bot_Running_Details.xlsx và trả về DataFrame.
    Nếu lỗi hoặc không có file, trả về None.
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Lỗi khi load trạng thái bot: {e}")
        return None

def update_bot_running_details_by_thread(thread_id, update_dict, file_path="Bot_Running_Details.xlsx"):
    """
    Cập nhật một dòng theo thread_id (giá trị cột 'Thread') trong file Bot_Running_Details.xlsx.
    - thread_id: số Thread (giá trị cột 'Thread')
    - update_dict: dict {tên_cột: giá_trị_mới}
    - file_path: đường dẫn file Excel
    """
    with excel_write_lock:
        try:
            df = pd.read_excel(file_path)
            idx = df.index[df['Thread'] == thread_id].tolist()
            if not idx:
                print(f"Không tìm thấy Thread {thread_id} trong file {file_path}")
                return
            row_idx = idx[0]
            for col, val in update_dict.items():
                if col in df.columns:
                    # Ép kiểu cột về object trước khi gán giá trị không phải số
                    df[col] = df[col].astype(object)
                    df.at[row_idx, col] = val
            df.to_excel(file_path, index=False)
        except Exception as e:
            print(f"Lỗi khi cập nhật trạng thái bot theo thread: {e}")

def delete_bot_running_details_by_thread(thread_id, file_path="Bot_Running_Details.xlsx"):
    """
    Xóa một dòng theo thread_id (giá trị cột 'Thread') trong file Bot_Running_Details.xlsx.
    - thread_id: số Thread (giá trị cột 'Thread')
    - file_path: đường dẫn file Excel
    """
    try:
        df = pd.read_excel(file_path)
        idx = df.index[df['Thread'] == thread_id].tolist()
        if not idx:
            print(f"Không tìm thấy Thread {thread_id} trong file {file_path}")
            return
        df = df.drop(idx[0])
        df.to_excel(file_path, index=False)
    except Exception as e:
        print(f"Lỗi khi xóa trạng thái bot theo thread: {e}")