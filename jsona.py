import json
import os
import shutil
from tempfile import NamedTemporaryFile

import typing


class Jsona:
    def build_ends_with(self, data: str, ends: str) -> str:
        return data if data.endswith(ends) else f'{data}{ends}'
    

    def default_error_proceed(error: Exception):
        print(f'ERROR: {error}')

        return True


    def __init__(self, path_file: str, name_file: str, error_proceed: typing.Callable[[Exception], bool] = default_error_proceed):
        self.path = os.path.join(path_file, name_file)

        self.encoding = 'utf8'
        self.error_proceed = error_proceed
    

    def save_json(self, data : dict, sort : bool = False, correct_ascii: bool = False, ident = None) -> bool:
        mode = 'w'

        try:
            with NamedTemporaryFile(mode = mode, encoding = self.encoding, delete = False) as temp_file:
                json.dump(obj = data, fp = temp_file, sort_keys = sort, indent = ident, ensure_ascii = not correct_ascii)

                shutil.move(src = temp_file.name, dst = self.path)

            return {'success': True}
        except Exception as e:
            os.remove(temp_file.name)
            self.error_proceed(e)

        return {'success': False}
                

    def return_json(self) -> dict:
        mode = 'r'
        error = None

        try:
            with open(file = self.path, mode = mode, encoding = self.encoding) as file_object:
                data = json.loads(file_object.read())

                return {"success": True, "data": data}
        except Exception as e:
            error = e
            self.error_proceed(error)

        return {"success": False, "except_type": type(error).__name__, "except": error.filename}


if __name__ == '__main__':
    jsona = Jsona('', 'save.json')

    jsona.save_json({'afaw': 12})