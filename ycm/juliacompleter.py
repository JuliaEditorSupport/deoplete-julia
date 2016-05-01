
import sys
sys.path.append("../../../..") #Make ycmd in-scope




from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycmd.completers.completer import Completer



class JuliaCompleter( Completer ):

    def __init__( self, user_options ):
        super( JuliaCompleter, self ).__init__( user_options )

    def ComputeCandidatesInner( self, request_data ):
        current_line = request_data[ 'line_value' ]
        start_codepoint = request_data[ 'start_codepoint' ] - 1
        filepath = request_data[ 'filepath' ]
        filetypes = request_data[ 'file_data' ][ filepath ][ 'filetypes' ]
        line = current_line[ : start_codepoint
        working_dir = request_data.get( 'working_dir' )



