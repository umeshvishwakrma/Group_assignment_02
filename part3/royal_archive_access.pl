/*
Problem 3: Royal Archive Access Verification
Method: First Order Predicate Logic and Resolution Refutation

Run with SWI-Prolog:
    swipl -q -s royal_archive_access.pl -g prove_mira -t halt

Goal:
    trusted(mira)
*/

/* =========================================================
   Step 1: First Order Predicate Logic representation
   =========================================================

   Predicates:
     archivist(Person)
     verifies(Person, Record)
     trusted(Person)
     has_access(Person, Record)
     permitted_to_inspect(Person, Record)
     inspects(Person, Record)
     finds_hidden_mark(Person, Record)
     stored_in_royal_archive(Record)
     sealed(Record)

   Constants: mira, scroll_7
   Variables: X = person, R = record

   Rules:
   R1: forall X,R:
       (archivist(X) AND verifies(X,R)) -> trusted(X)

   R2: forall X,R:
       (trusted(X) AND has_access(X,R) AND sealed(R))
       -> permitted_to_inspect(X,R)

   R3: forall X,R:
       (inspects(X,R) AND finds_hidden_mark(X,R))
       -> verifies(X,R)

   R4: forall R:
       stored_in_royal_archive(R) -> sealed(R)

   Facts:
   F1: stored_in_royal_archive(scroll_7)
   F2: has_access(mira, scroll_7)
   F3: inspects(mira, scroll_7)
   F4: finds_hidden_mark(mira, scroll_7)
   F5: archivist(mira)
*/

/* Prolog representation of the given facts and rules. */
archivist(mira).
has_access(mira, scroll_7).
inspects(mira, scroll_7).
finds_hidden_mark(mira, scroll_7).
stored_in_royal_archive(scroll_7).

trusted(X) :-
    archivist(X),
    verifies(X, _Record).

permitted_to_inspect(X, R) :-
    trusted(X),
    has_access(X, R),
    sealed(R).

verifies(X, R) :-
    inspects(X, R),
    finds_hidden_mark(X, R).

sealed(R) :-
    stored_in_royal_archive(R).

/* =========================================================
   Step 2: Negation of the goal
   =========================================================

   Goal: trusted(mira)
   Negated goal: not trusted(mira)
*/
negated_goal(neg(trusted(mira))).

/* =========================================================
   Steps 3-6: Conversion before CNF
   =========================================================

   Implication removal:
       A -> B  becomes  not A OR B

   Negation movement:
       The resulting formulas already have negations only
       in front of individual predicates (NNF).

   Standardization apart:
       Use separate variables for each rule:
       R1: X1,R1; R2: X2,R2; R3: X3,R3; R4: R4.

   Skolemization:
       No existentially quantified variables occur, so no
       Skolem constants or functions are required.
*/

/* =========================================================
   Step 7: Clause form (CNF)
   =========================================================

   C1: not archivist(X) OR not verifies(X,R) OR trusted(X)
   C2: not trusted(X) OR not has_access(X,R) OR not sealed(R)
       OR permitted_to_inspect(X,R)
   C3: not inspects(X,R) OR not finds_hidden_mark(X,R)
       OR verifies(X,R)
   C4: not stored_in_royal_archive(R) OR sealed(R)

   C5-C9: the five facts
   C10:   negated goal
*/

cnf_clause(c1,
    [neg(archivist(X)), neg(verifies(X, R)), trusted(X)]).

cnf_clause(c2,
    [neg(trusted(X)), neg(has_access(X, R)), neg(sealed(R)),
     permitted_to_inspect(X, R)]).

cnf_clause(c3,
    [neg(inspects(X, R)), neg(finds_hidden_mark(X, R)),
     verifies(X, R)]).

cnf_clause(c4,
    [neg(stored_in_royal_archive(R)), sealed(R)]).

cnf_clause(c5, [stored_in_royal_archive(scroll_7)]).
cnf_clause(c6, [has_access(mira, scroll_7)]).
cnf_clause(c7, [inspects(mira, scroll_7)]).
cnf_clause(c8, [finds_hidden_mark(mira, scroll_7)]).
cnf_clause(c9, [archivist(mira)]).
cnf_clause(c10, [neg(trusted(mira))]).

/* =========================================================
   Step 8: Resolution implementation and execution
   ========================================================= */

/* Two literals are complementary if one is the negation
   of the other. */
complementary(neg(Literal), Literal).
complementary(Literal, neg(Literal)).

/* Resolve two clauses. copy_term keeps their variables
   separate before unification. */
resolve_pair(ClauseA, ClauseB, Resolvent) :-
    copy_term((ClauseA, ClauseB), (A, B)),
    select(Literal, A, RemainingA),
    complementary(Literal, Opposite),
    select(Opposite, B, RemainingB),
    append(RemainingA, RemainingB, Combined),
    sort(Combined, Resolvent).

show_step(Number, Description, Resolvent) :-
    format('Step ~w: ~w~n', [Number, Description]),
    format('         Resolvent = ~w~n~n', [Resolvent]).

prove_mira :-
    nl,
    writeln('ROYAL ARCHIVE: RESOLUTION REFUTATION'),
    writeln('Target: trusted(mira)'),
    writeln('Negated target: neg(trusted(mira))'),
    nl,

    /* C3 resolved with fact C7. */
    resolve_pair(
        [neg(inspects(mira, scroll_7)),
         neg(finds_hidden_mark(mira, scroll_7)),
         verifies(mira, scroll_7)],
        [inspects(mira, scroll_7)],
        R1),
    show_step(1,
        'Resolve C3 with the fact inspects(mira, scroll_7).',
        R1),

    /* Result resolved with fact C8. */
    resolve_pair(
        R1,
        [finds_hidden_mark(mira, scroll_7)],
        R2),
    show_step(2,
        'Resolve with finds_hidden_mark(mira, scroll_7).',
        R2),

    /* C1 resolved with fact C9. */
    resolve_pair(
        [neg(archivist(mira)),
         neg(verifies(mira, scroll_7)),
         trusted(mira)],
        [archivist(mira)],
        R3),
    show_step(3,
        'Resolve C1 with the fact archivist(mira).',
        R3),

    /* Result of Step 3 resolved with result of Step 2. */
    resolve_pair(R3, R2, R4),
    show_step(4,
        'Resolve with the result of Step 2, verifies(mira, scroll_7).',
        R4),

    /* Resolve trusted(mira) with the negated goal. */
    resolve_pair(R4, [neg(trusted(mira))], Empty),
    show_step(5,
        'Resolve with the negated goal neg(trusted(mira)).',
        Empty),

    ( Empty == [] ->
        writeln('SUCCESS: Empty clause [] derived.'),
        writeln('Therefore the negated goal is inconsistent with the knowledge base.'),
        writeln('Hence trusted(mira) is proved.')
    ;
        writeln('FAILURE: Empty clause was not derived.')
    ).
