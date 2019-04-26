from quart import Quart

from webargs import fields
from quartparser import use_args

app = Quart(__name__)

hello_args = {
    'name': fields.Str(required=True)
}

@app.route('/')
@use_args(hello_args)
def index(args):
    return 'Hello ' + args['name']

app.run()
