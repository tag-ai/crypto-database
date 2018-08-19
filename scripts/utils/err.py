from emailer import send_email
import datetime

def log_errors(e,
               func_name, script_name, dir_path,
               args, arg_names):
    """
    Log errors to file errors.log and prints them to screen.

    fun_name : str
        Name of function raising error.

    script_name : str
        Name of script raising error ( os.path.split(__file__)[-1] ).

    dir_path : str
        Path of file raising error.

    args : list
        List of arguments.

    arg_names : str
        Argument names (comma separated).
    """

    # Write to stdout
    print('Exception raised in {}.py'.format(script_name))
    msg = []
    _arg_names = [a.strip() for a in arg_names.splt(',')]
    for name, var in zip(_arg_names, args):
        msg.append('{}={}'.format(name, var))
    print('\n'.join(msg))
    print(e)

    # Write to file
    with open(os.path.join(dir_path, 'errors_{}.log'.format(script_name)), 'a+') as f:
        f.write('Exception raised in {} function of {}.py.\n'.format(func_name, script_name))
        f.write('Dumping vars:\n')
        f.write('\n'.join(msg) + '\n')
        f.write('Dumping error:\n')
        f.write('{}\n'.format(e))
        f.write('-' * 25 + '\n')

    # Send email
    send_email(subject='Exception raised in {}.py'.format(script_name),
               msg=('Exception raised in {} function of {}.py. '
                    '<br><br><b>Date</b> = {}'
                    '<br><br><b>Error:</b> <br>{}'
                    '<br><br><b>Vars:</b> <br>{}')\
                    .format(func_name, script_name,
                            datetime.datetime.utcnow(), e, '<br>'.join(msg)),
               destination_emails=['tag.ai.tech@gmail.com'])

