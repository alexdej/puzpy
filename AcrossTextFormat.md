# Creating Across puzzles using Across Lite

## Copyright Notice

This is a copyrighted document owned by Literate Software Systems.
Distribution of this document does not confer any rights to any entity
other than to enable creation of crosswords exclusively for use with
Across Lite or any other software explicitly authorized by Literate
Software Systems. Any other use of this document or the contents in
whole or in part is prohibited.

## User Guide

There are two Across crossword formats - a TEXT version and a BINARY
version. The BINARY version is the one used for online distribution. It
can be read by Across Lite on any platform and contains checksums to
ensure the integrity of the puzzle during copying and downloading
operations. Solution scrambling is also possible in this format. Across
Lite saves worked-on puzzles in this format. The TEXT version is only
used for creating puzzles in Across BINARY format.

Since the release of Across Lite v2, there are two versions of the TEXT
crossword format. While the older TEXT version can be used by Across
Lite v2, the newer v2 TEXT version cannot be read by versions of Across
Lite prior to v2. The newer version is designed to create rebus puzzles
i.e., puzzles with use of special characters/symbols, multiple letters
in the same cell, etc.

**Note:** The BINARY puzzles created using either TEXT version or any
version of Across Lite program can be opened by any other Across Lite
version.

The following is a summary of the usage of the two versions:

### To create a BINARY (.puz) puzzle without rebus 

- Use the older TEXT format and any Across Lite (v2.x or earlier)
  program to read it and save in the BINARY (.puz) format. OR

- Use the new v2 TEXT format and Across Lite v2.x program and save in
  the BINARY (.puz) format

### To create a BINARY (.puz) puzzle with rebus 

• Use the new v2 TEXT format and Across Lite v2 program and save in the
BINARY (.puz) format

The basic steps for creating a BINARY (.puz) file using either version
are:

1.  Create a TEXT file containing the crossword information using a text
    editor (Notepad, SimpleText, vi, etc.) or a word processor (Word,
    WordPerfect, Frame, etc.) that can output the file as simple text.
    The information is entered using a specific format as described
    below. Check the information for spelling, errors, etc. Save the
    file with a .TXT filename extension.

2.  Open the TEXT file using Across Lite. You can use the File->Open
    command or in versions that support drag and drop, you can drop the
    file on an open Across Lite window or icon. In most cases, you must
    use Across Lite on the same platform as the platform in which the
    TEXT file was created. So, for example, if the TEXT file was created
    using Windows Notepad, use the Windows version of Across Lite. If it
    was created using SimpleText on a Mac, use the Mac version of Across
    Lite.

3.  If there are any errors in the TEXT description, Across Lite will
    refuse to load the puzzle and give diagnostic error messages. This
    is to ensure that any problems such as missing clues, incorrect
    solution grid, extra/repeated clues, etc., are caught **before
    distribution**. If there are no errors, the puzzle will be loaded
    into Across Lite.

4.  Optionally, scramble the solution using the Solution->Scramble
    command, if desired. Record the scramble key elsewhere for
    publication later.

5.  Save the puzzle. Across Lite will only save in the BINARY format.
    The filename extension .PUZ is strongly recommended for the BINARY
    format and is the default. The saved file is now ready for
    distribution and can be read by any version of Across Lite on any
    platform.

## Creating the TEXT file

The rest of the document describes the procedure for creating the TEXT
format descriptions. First the older TEXT version is described followed
by the extensions provided for in the v2 TEXT version.

### Older TEXT version (prior to v2) 

The crossword information should be entered using the following
template. The tags that mark each section are important and must be in
the same order as below.

`<ACROSS PUZZLE>`<br>
`<TITLE>`<br>
&emsp;...puzzle title/theme here in a single line... (or leave a blank line)<br>
`<AUTHOR>`<br>
&emsp;...puzzle author/editor here in a single line... (or leave a blank line)<br>
`<COPYRIGHT>`<br>
&emsp;...puzzle copyright notice here in a single line. A © will be automatically added at the beginning... (or leave a blank line)<br>
`<SIZE>`<br>
&emsp;...grid size as No. of columns x No. of rows (e.g., 15x15). Must provide this information. x must be lower case.<br>
`<GRID>`<br>
&emsp;...Use one line for each row in the grid. Enter solution letter or period(.) for black square. No spaces between the characters. If solution is to be omitted use X (upper case) for **all** solution letters. To create the puzzle as a diagramless, use colon (:) for black squares instead of the period.<br>
`<ACROSS>`<br>
&emsp;... List Across clues one **entire clue per line** in increasing order of clue numbers. **Do not** enter the clue number itself.<br>
`<DOWN>`<br>
&emsp;... List Down clues one **entire clue per line** in increasing order of clue numbers. **Do not** enter the clue number itself.<br>
`<NOTEPAD>`<br>
&emsp;.... Notepad entry for the puzzle here. This section is optional and can be entirely omitted. All spaces and line breaks are preserved. A maximum of 1023 characters can be entered here. Longer entries will be truncated to the first 1023 characters.<br>

A sample file with the complete description of a 15x15 puzzle is
included below. Note that leading spaces/tabs are ignored in all
sections except the notepad.

```
<ACROSS PUZZLE>
<TITLE>
    Politics: Who, what, where and why
<AUTHOR>
    Created by Avalonian
<COPYRIGHT>
    1995 Literate Software Systems
<SIZE>
    15x15
<GRID>
    FATE.AWASH.AWOL
    LIES.CURIO.SHOE
    ELECTORATE.SIZE
    ASS.ERST.DIETED
    ...CENT.HOSTESS REFITS.JEWISH..
    ARITH.KERNS.OAF
    NILE.ANNES.DUPE
    DEI.OVENS.LOSER
    ..BODILY.RACERS GLUTEAL.PEPS...
    RESIST.SLUE.SKI
    OTTO.REPUBLICAN
    OMES.IRATE.RAMS
    MERE.XENON.ABET
<ACROSS>
    Destiny
    Above water, barely
    Deserter
    True ____ : Arnold S. movie Novel or rare item
    If the ____ fits, ...
    Favorite group of 53 across
    EEE with 16 across
    Midsummer's Night Dream character
    Formerly
    Ate sparingly
    Monetary unit
    She entertains guests
    Make ready for use again
    Yiddish, informally
    Math. subject
    Parts of typeset characters
    Clod
    Egyptian river
    Bancroft and Archer
    Fool
    God in latin
    Pizza place fixtures
    Sometimes a dieter is one
    Physical
    Some kinds of snakes
    Of posterior muscles
    Raises one's spirits
    Block
    Swing about
    ____ slopes
    A dog's name
    GOP member
    Of masses
    Angry
    Strikes violently
    Just
    Inert gas
    Encourage
<DOWN>
    Biting insect
    Troubles
    Golf equipments
    Computer keyboard key
    Oak seed or fruit
    Sausage
    I smell ____
    Squat
    Community dances Owned property
    House on Pennsylvania Ave.
    Seeps
    City NE of Manchester
    Subject of dentistry
    Wife of Asiris
    Use reference
    "____, Johnny!"
    South African currency unit
    Canal or Lake
    Delaying tactic of 53 across
    Spinning ____
    Toll
    One who mimics
    Bearers : comb. form
    Female pilot
    Medics
    Homages
    Coat part
    Idle
    Type of sandwich
    Clean and care for
    "____ through!"
    Smallest planet of the Sun
    Cover
    One who works despite a strike
    Glacial ridge Org.
    Before
    Tax break savings account
<NOTEPAD>
    This is an example notepad entry with two lines in it.
```

### V2 TEXT Version 

This version is very similar to the older version except for the
following changes/extensions. Note this version cannot be read by
versions of Across Lite prior to v2.x

1.  The file starts with `<ACROSS PUZZLE V2>` instead of `<ACROSS PUZZLE>`

2.  The `<GRID>` section is extended with the following:

    1. The solution letters can be any of

            i. Alphabets A .. Z (as before in the older version)
            ii.  Numbers 0 .. 9
            iii.  Special characters @, \#, $, %, &, +, ?
            iv.  Lower case alphabets a .. z

        i-iii denote letters and characters that form the solution for the
        puzzle for the specified cell in the `<GRID>` section. (iv) is
        equivalent to (i) if there is no `<REBUS>` section described
        later.
        
        If there is a `<REBUS>` section later, the meaning of numbers and
        lower case alphabets can be modified and additional symbols can be
        introduced.
        
        Across Lite versions prior to v2.x support alphabets but not numbers
        or special characters. When the .puz file is created with the above
        extensions for v2.x, the file can be read into the old versions but
        the solution will be replaced with the first character representing
        the number or character as follows:
    
            1 = O, 2 = T, 3 = T, 4 = F, 5 = F, 6 = S, 7 = S, 8 = E, 9 = N, 0 = Z
            @ = A, # = H, $ = D, % = P, & = A, + = P, ? = Q
    
        The numbers and special characters will not be seen on the grid or in
        print outs in the older version.
    
        In Across Lite v2.x, these characters can be entered directly from the
        keyboard and will appear as such on the program window as well as in
        any print outs.

3.  There is an optional new section immediately following the
    `<GRID>` section with the header `<REBUS>`. This section can
    be used in v2 TEXT format only.

    This section has the following format

    ```
    <REBUS> flag 
    list…
    marker:<extended solution>:<short solution>
    …
    marker:<extended solution>:<short solution>
    ```

    as explained below. If this section is present, at least one line
    containing either the flag list or a marker line should be present.
    The flag list line is optional.

    ### FLAG LIST 

    The flag list specifies certain special attributes of the crossword
    with key words separated by semicolons(;). Currently, only one flag
    `MARK` is supported.

    #### MARK

    This flag specifies that all cells that have lower case alphabets in
    the `<GRID>` section must be marked with a circle in the puzzle
    that is created.

    **Note**: Previously, to create a puzzle with certain cells pre-marked
    with a circle, one had to create a regular puzzle, load it into Across
    Lite program and use the * key on each cell where the circle needed
    to appear and then save it. This provides a more convenient method
    where each such cell can be specified in the `<GRID`> section with
    a lower case alphabet and the MARK flag specified in the `<REBUS`>
    section to automatically create a puzzle with the appropriate cells
    circled.

    For example, the following `<GRID`> and `<REBUS`> section in
    the TEXT format will result in a puzzle identical to the full example
    above but with all the four corner cells circled in the produced .puz
    file.

    ```
    <ACROSS PUZZLE V2>
    <TITLE>
        Politics: Who, what, where and why
    <AUTHOR>
        Created by Avalonian
    <COPYRIGHT>
        1995 Literate Software Systems
    <SIZE>
        15x15
    <GRID>
        fATE.AWASH.AWOl<-- Note lower case letters at the ends
        LIES.CURIO.SHOE
        ELECTORATE.SIZE
        ASS.ERST.DIETED
        ...CENT.HOSTESS
    REFITS.JEWISH..
        ARITH.KERNS.OAF
        NILE.ANNES.DUPE
        DEI.OVENS.LOSER
        ..BODILY.RACERS
    GLUTEAL.PEPS...
        RESIST.SLUE.SKI
        OTTO.REPUBLICAN
        OMES.IRATE.RAMS
        mERE.XENON.ABEt<-- Note lower case letters at the ends
    <REBUS>
    MARK;
    <ACROSS>
    … the rest as before
    ```

    ### MARKER LINES 

    The correct way to visualize marker lines is as footnotes for a piece
    of text (in this case the <GRID> section). The marker lines
    provide additional information for the annotated cells (with the
    marker characters) in the <GRID> section.

    Any of the characters allowed in the <GRID> section can be used
    as a marker with

    extended meaning. The same extended meaning applies to all the markers
    annotated with the same character in the <GRID> section.

    We will describe below a number of use case scenarios for using this
    section for quick understanding of what is possible

    1. To create a puzzle with the word ESP as the solution in a single
    cell at multiple locations

        ```
        <GRID>
            UFO.D1OTS.SIDLE
            TIN.ERNIE.TH1IS
            UNS.BITER.ROLFE
            R1IRATOR.PUPAE.
            NUDER...GUTSILY
        …
        <REBUS>
        1:ESP:E
        <ACROSS>
        ```

        etc.

        Note use of 1 as the marker at 3 cells above in the partial grid. The
        `<REBUS`> section describes what this annotation means. **Note**:
        If the `<REBUS`> section did not exist, then the above puzzle
        would have been generated as if 1 was the solution in those cells.

        The above description creates a puzzle where **all** the cells marked
        with1 have the multiple letters ESP as the solution in Across Lite
        v2.x and just the character E as the solution when read opened by
        previous Across Lite versions.

        The marker line in the REBUS section has three parts separated by
        colons. The first is the (“footnote”) marker that indicates to which
        cells that line applies to. In this example it is the number 1. The
        second part denotes the solution (ESP in this case) for v2 puzzle that
        allows multiple characters. The third part denotes the single
        character solution that will be used in earlier versions of Across
        Lite (E in this case). The third part **must** be a single character.

    2. To create a puzzle with different multi-letter answers in
    different cells

        ```
        <GRID>
        …
            FREN1NDO1NA.UMA
            ...GAD.UPS.I2IT
            SO3ST.LPS.AN2AL
        …
        <REBUS>
        1:CHI:C
        2:NU:N
        3:PHI:P
        ```

        This puzzle uses the Greek alphabets (expressed in English) at various
        places. Each of the markers denote the use of one such characters and
        apply to all occurrences of that marker in the grid. As in the
        previous example, the third part of the markers denotes the single
        characters to be used for older versions of Across Lite.

    3. Creating a puzzle with symbols other than the special characters
    allowed in the keyboard.

        ```
        <GRID>
        …
            MONK1DWITH.STAS
        …
            ABA.NOW2HIS.ISA
        …
        <REBUS>
        1:[75]:E
        2:[89]:H
        ```

        This puzzle uses two graphic symbols 👁 and 🎔 representing EYE and
        HEART. The numbers used in the `<REBUS>` section refers to the
        character codes in the Webdings font table (provided separately). The
        list of available symbols can be seen via Character Map program in
        Windows or the Character Palette in Mac OS X.

### Known Limitations 

The current format does not support use of different letters or words
in the same cell depending on whether it is an ACROSS solution or a
DOWN solution.

The symbols can be displayed only on computers that have the Webdings
font installed. This is part of the standard distribution in most
Windows and Mac OS X versions. The rest will revert to the use of the
single corresponding letter.

