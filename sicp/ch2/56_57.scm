(define (variable? v)
  (symbol? v))

(define (same-variable? a b)
  (and (variable? a) (variable? b) (eq? a b)))

(define (expression-type? sym)
  (lambda (exp)
    (and (pair? exp) (eq? (car exp) sym))))

(define sum? (expression-type? '+))

(define (=number? a b)
  (and (number? a) (number? b) (= a b)))

(define (single-operand? operands)
  (= (length operands) 1))

(define (make-sum a . b)
  (if (single-operand? b)
      (let ((b (car b)))
        (cond ((=number? a 0) b)
              ((=number? b 0) a)
              ((and (number? a) (number? b))
               (+ a b))
              (else
                (list '+ a b))))
      (cons '+ (cons a b))))

(define (addend exp)
  (cadr exp))

(define (augend exp)
  (let ((tail-operand (cddr exp)))
    (if (single-operand? tail-operand)
        (car tail-operand)
        (apply make-sum tail-operand))))

(define product? (expression-type? '*))

(define (make-product a . b)
  (if (single-operand? b)
      (let ((b (car b)))
        (cond ((or (=number? a 0) (=number? b 0)) 0)
              ((=number? a 1) b)
              ((=number? b 1) a)
              ((and (number? a) (number? b)) (* a b))
              (else
                (list '* a b))))
      (cons '* (cons a b))))

(define (multiplicand exp)
  (cadr exp))

(define (multiplier exp)
  (let ((tail-operand (cddr exp)))
    (if (single-operand? tail-operand)
        (car tail-operand)
        (apply make-product tail-operand))))

(define (pow base exp)
  (define (iter b e result)
    (cond ((= e 0) result)
          ((even? e)
           (iter (* b b) (/ e 2) result))
          (else
            (iter b (- e 1) (* result b)))))
  (iter base exp 1))

(define exponentiation? (expression-type? '**))

(define (make-exponentiation base exp)
  (list '** base exp))

(define (base exp)
  (cadr exp))

(define (exponent exp)
  (caddr exp))

(define (deriv exp var)
  (cond ((number? exp) 0)
        ((variable? exp) (if (same-variable? exp var) 1 0))
        ((sum? exp) (make-sum (deriv (addend exp) var)
                              (deriv (augend exp) var)))
        ((product? exp)
         (make-sum
           (make-product (multiplier exp)
                         (deriv (multiplicand exp) var))
           (make-product (deriv (multiplier exp) var)
                         (multiplicand exp))))
        ((exponentiation? exp)
         (let ((b (base exp))
               (e (exponent exp)))
           (make-product e
                         (make-product
                           (make-exponentiation b (make-sum e -1))
                           (deriv b var)))))
        (else
          (error "unknown expression type: DERIV" exp))))
