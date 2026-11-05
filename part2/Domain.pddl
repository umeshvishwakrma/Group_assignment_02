(define (domain mars-rover)
  (:requirements :strips :typing)

  (:types location rock bay)

  (:predicates
    (rover-at ?l - location)
    (connected ?from ?to - location)      ; directed edge
    (rock-at ?r - rock ?l - location)
    (drill-at ?l - location)
    (has-drill)                           ; rover carries the drill
    (soft ?r - rock)
    (hard ?r - rock)
    (bay-empty ?b - bay)
    (in-bay ?r - rock ?b - bay)
  )

  ;; Move along a directed edge
  (:action move
    :parameters (?from ?to - location)
    :precondition (and (rover-at ?from) (connected ?from ?to))
    :effect (and (rover-at ?to) (not (rover-at ?from)))
  )

  ;; Pick up the drill (kept for the rest of the mission)
  (:action pick-drill
    :parameters (?l - location)
    :precondition (and (rover-at ?l) (drill-at ?l))
    :effect (and (has-drill) (not (drill-at ?l)))
  )

  ;; Collect a soft rock into an empty bay
  (:action collect-soft
    :parameters (?r - rock ?l - location ?b - bay)
    :precondition (and (rover-at ?l) (rock-at ?r ?l) (soft ?r) (bay-empty ?b))
    :effect (and (in-bay ?r ?b) (not (rock-at ?r ?l)) (not (bay-empty ?b)))
  )

  ;; Collect a hard rock (needs the drill)
  (:action collect-hard
    :parameters (?r - rock ?l - location ?b - bay)
    :precondition (and (rover-at ?l) (rock-at ?r ?l) (hard ?r) (has-drill) (bay-empty ?b))
    :effect (and (in-bay ?r ?b) (not (rock-at ?r ?l)) (not (bay-empty ?b)))
  )

  ;; Drop a rock from a bay at the current location
  (:action deposit
    :parameters (?r - rock ?l - location ?b - bay)
    :precondition (and (rover-at ?l) (in-bay ?r ?b))
    :effect (and (rock-at ?r ?l) (bay-empty ?b) (not (in-bay ?r ?b)))
  )
)
