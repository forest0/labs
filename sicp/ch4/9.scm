; example usage
;
; syntax
; (while (condition) (body))
;
; e.g.
; (let ((i 1))
;   (while (< i 5)
;          (display i)
;          (set! i (+ i 1))))
;
; which is equivalent to
; (let ((i 1))
;   (begin (define (loop)
;            (if (< i 5)
;                (begin (display i)
;                       (set! i (+ i 1)))
;                'done))
;          (loop)))

(define (while->derived exp)
  (define (while-condition exp) (cadr exp))
  (define (while-body exp) (cddr exp))
  (make-begin (list
                ; deinfe loop
                (make-define '(loop)
                             (list
                               (make-if (while-condition exp)
                                        (make-begin (list
                                                      (make-begin (while-body exp))))
                                        'done)))
                ; enter loop
                '(loop))))

; loop until satisfying condition
(define (until-derived exp)
  (define (until-condition exp) (cadr exp))
  (define (until-body exp) (cddr exp))
  (while->derived (cons 'while
                        (cons (list 'not (until-condition exp))
                              (until-body exp)))))
