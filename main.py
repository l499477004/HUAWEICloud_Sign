import argparse
import asyncio
import inspect
import logging
from importlib import import_module

DEFAULT_FORMATTER = '%(asctime)s[%(filename)s:%(lineno)d][%(levelname)s]:%(message)s'
logging.basicConfig(format=DEFAULT_FORMATTER, level=logging.INFO)


def script_main(params):
    client = params.get('client')
    module = import_module('.'.join(['clients', client]))
    loop = asyncio.get_event_loop()
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and str(obj).find('clients') != -1:
            instance = obj()
            func = getattr(instance, 'run')
            try:
                loop.run_until_complete(func(**params))
            except Exception as e:
                logging.warning(e)
                exit(1)
            finally:
                loop.close()
                exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client')
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--iam', action='store_true')
    parser.add_argument('--parent')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    params = vars(args)
    params['headless'] = True if not params['headless'] else False
    script_main(params)


if __name__ == '__main__':
    main()
