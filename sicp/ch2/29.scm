(define (make-mobile left right)
  (list left right))

(define (left-branch m)
  (car m))

(define (right-branch m)
  (cadr m))

(define (make-branch length structure)
  (list length structure))

(define (branch-length b)
  (car b))

(define (branch-structure b)
  (cadr b))

(define (total-weight m)
  (+
    (branch-weight (left-branch m))
    (branch-weight (right-branch m))))

(define (hangs-another-mobile? b)
  (pair? (branch-structure b)))

(define (branch-weight b)
  (if (hangs-another-mobile? b)
      (total-weight (branch-structure b))
      (branch-structure b)))

(define (branch-torque b)
  (*
    (branch-length b)
    (branch-weight b)))

(define (same-torque b1 b2)
  (=
    (branch-torque b1)
    (branch-torque b2)))

(define (branch-balance? b)
  (if (hangs-another-mobile b)
      (mobile-balance? (branch-structure b))
      #t))

(define (mobile-balance? m)
  (let ((lb (left-branch m))
        (rb (right-branch m)))
    (and
      (same-torque lb rb)
      (branch-balance? lb)
      (branch-balance? rb))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; list -> cons
; the following procedures need change to
; 
; (define (make-mobile left right)
;   (cons left right))
; 
; (define (make-branch length structure)
;   (cons length structure))
; 
; (define (right-branch m)
;   (cdr m))
; 
; (define (branch-structure b)
;   (cdr b))
