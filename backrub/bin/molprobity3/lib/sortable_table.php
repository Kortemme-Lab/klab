<?php # (jEdit options) :folding=explicit:collapseFolds=1:
/*****************************************************************************
    Formats sortable tables stored as nested PHP arrays.
    See code for "documentation" of the format, which may evolve.
*****************************************************************************/

#{{{ formatSortableTable - convert PHP array into HTML string
############################################################################
/**
* $table        the data structure
* $url          base URL to use for links
* $col          column to sort on, -1 (the default) means no sort
* $direction    sort direction, 1 is ascending (the default), -1 is descending.
*/
function formatSortableTable($table, $url, $col = -1, $direction = 1)
{
    $s = '';
    // Prepare $url to have (more) parameters tacked on the end.
    if(strpos($url, '?') === false) $url .= '?';
    else                            $url .= '&';
    
    // Stupid song and dance b/c PHP doesn't have a stable sort function like mergesort.
    // Arrays are passed by value, so we're modifying a copy, so it's OK.
    $rows = &$table['rows'];
    $i = 1;
    foreach($rows as $key => $row)
        $rows[$key]['@@NATIVE@@'] = $i++;
    // Custom "lambda" sort function -- essentially, curried on the name of the sort field and direction
    // Commented out $direction component of native fallback b/c native should always be same order
    $mySortFunc = create_function('$a,$b', "
        if(!isset(\$a[$col]['sort_val']))
        {
            if(!isset(\$b[$col]['sort_val']))   return /*$direction**/(\$a['@@NATIVE@@'] - \$b['@@NATIVE@@']);
            else                                return 1;
        }
        elseif(!isset(\$b[$col]['sort_val']))   return -1;
        elseif(\$a[$col]['sort_val'] < \$b[$col]['sort_val']) return -($direction);
        elseif(\$a[$col]['sort_val'] > \$b[$col]['sort_val']) return $direction;
        else                                    return /*$direction**/(\$a['@@NATIVE@@'] - \$b['@@NATIVE@@']);
    ");
    // This check isn't necessary (sort will be done correctly) but makes me feel better...
    if($col != -1)
        uasort($rows, $mySortFunc);
    
    $s .= $table['prequel'];
    $s .= "\n";
    $s .= "<table width='100%' cellspacing='1' border='0'>\n";
    
    // Headers are mixed in with rows and so appear below.
    
    $row_counter = 0;
    $color = MP_TABLE_ALT1;
    foreach($table['rows'] as $row)
    {
        // Repeat headers every so many rows:
        if($row_counter++ % 20 == 0)
        {
            foreach($table['headers'] as $header)
            {
                $s .= "<tr align='center' bgcolor='".MP_TABLE_HIGHLIGHT."'>";
                $i = 0;
                foreach($header as $cell)
                {
                    $s .= "<td>";
                    $sort_dir = ($i == $col ? -$direction : $cell['sort']);
                    if($cell['sort']) $s .= "<a href='{$url}sort_col=$i&sort_dir=$sort_dir'>";
                    $s .= $cell['html'];
                    if($cell['sort']) $s .= "</a>";
                    $s .= "</td>";
                    $i++;
                }
                $s .= "</tr>\n";
            }
        }
        
        // Normal rows:
        $s .= "<tr align='center' bgcolor='$color'>";
        foreach($row as $key => $cell)
        {
            // For some odd reason, 0 == '@@NATIVE@@' in PHP 5.0.4, so we use ===
            // Ah, because the string is being coerced to a number, which becomes zero...
            if($key === '@@NATIVE@@') continue;
            $s .= "<td";
            if($cell['color']) $s .= " bgcolor='$cell[color]'";
            $s .= ">$cell[html]</td>";
        }
        $s .= "</tr>\n";
        $color == MP_TABLE_ALT1 ? $color = MP_TABLE_ALT2 : $color = MP_TABLE_ALT1;
    }
    
    // Footers:
    foreach($table['footers'] as $footer)
    {
        $s .= "<tr align='center' bgcolor='".MP_TABLE_HIGHLIGHT."'>";
        foreach($footer as $cell)
        {
            $s .= "<td>$cell[html]</td>";
        }
        $s .= "</tr>\n";
    }
    $s .= "</table>\n";
    $s .= $table['sequel'];
    $s .= "\n";
    
    return $s;
}
#}}}########################################################################

#{{{ formatSortableTableJS - convert PHP array into HTML string
############################################################################
/**
* $table        the data structure
* $col          column to sort on, -1 (the default) means no sort
* $direction    sort direction, 1 is ascending (the default), -1 is descending.
*/
function formatSortableTableJS($table, $col = -1, $direction = 1)
{
    // Needs to actually insert the file for it to be self contained
    //$s = '<script src="js/sorttable.js" type="text/javascript"></script>';
    $s = "<script type='text/javascript'>\n";
    $s .= file_get_contents(MP_BASE_DIR.'/public_html/js/sorttable.js');
    $s .= "\n</script>\n";
    
    $s .= $table['prequel'];
    $s .= "\n";
    $s .= "<p><i>Live sorting requires JavaScript enabled and Safari 2, Firefox 1.5, or IE 6</i></p>\n";
    // requires that table have a unique id in order to sort
    $s .= "<table class='sortable' id='unique_tbl_id' width='100%' cellspacing='1' border='0'>\n";
    
    // Headers
    foreach($table['headers'] as $header)
    {
        $s .= "<tr align='center' bgcolor='".MP_TABLE_HIGHLIGHT."' class='sorttop'>";
        $i = 0;
        foreach($header as $cell)
        {
            $s .= "<td sortdir='$cell[sort]'>";
            $sort_dir = ($i == $col ? -$direction : $cell['sort']);
            $s .= $cell['html'];
            $s .= "</td>";
            $i++;
        }
        $s .= "</tr>\n";
    }
    
    // Normal rows:
    $row_counter = 0;
    $color = MP_TABLE_ALT1;
    foreach($table['rows'] as $row)
    {
        $s .= "<tr align='center' bgcolor='$color'>";
        foreach($row as $key => $cell)
        {
            $s .= "<td";
            if($cell['color']) $s .= " bgcolor='$cell[color]'";
            $s .= " sv='$cell[sort_val]'>$cell[html]</td>";
        }
        $s .= "</tr>\n";
        $color == MP_TABLE_ALT1 ? $color = MP_TABLE_ALT2 : $color = MP_TABLE_ALT1;
    }
    
    // Footers:
    foreach($table['footers'] as $footer)
    {
        $s .= "<tr align='center' bgcolor='".MP_TABLE_HIGHLIGHT."'>";
        foreach($footer as $cell)
        {
            $s .= "<td>$cell[html]</td>";
        }
        $s .= "</tr>\n";
    }
    $s .= "</table>\n";
    $s .= $table['sequel'];
    $s .= "\n";
    
    return $s;
}
#}}}########################################################################

#{{{ a_function_definition - sumary_statement_goes_here
############################################################################
/**
* Documentation for this function.
*/
//function someFunctionName() {}
#}}}########################################################################
?>
