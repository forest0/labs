(define (make-node item previous next)
  (define (set-previous-ptr! new-value)
    (set! previous new-value))
  (define (set-next-ptr! new-value)
    (set! next new-value))

  (define (set-item! new-value)
    (set! item new-value))

  (define (reset-links!)
    (set! previous '())
    (set! next '()))

  (define (dispatch m)
    (cond ((eq? m 'previous-ptr) previous)
          ((eq? m 'next-ptr) next)
          ((eq? m 'item) item)
          ((eq? m 'set-previous-ptr!) set-previous-ptr!)
          ((eq? m 'set-next-ptr!) set-next-ptr!)
          ((eq? m 'set-item!) set-item!)
          ((eq? m 'reset-links!) reset-links!)
          (else (error "Unknown operation -- DISPATCH of node" m))))
  dispatch)

(define (make-deque)
  (let ((front-ptr '())
        (rear-ptr '()))

    (define (empty-deque?)
      (null? front-ptr))

    (define (front-deque)
      (if (empty-deque?)
          (error "FRONT-DEQUE called with an empty deque")
          (front-ptr 'item)))
    (define (rear-deque)
      (if (empty-deque?)
          (error "REAR-DEQUE called with an empty deque")
          (rear-ptr 'item)))

    (define (front-insert-deque! item)
      (cond ((empty-deque?)
             (let ((new (make-node item '() '())))
               (set! front-ptr new)
               (set! rear-ptr new)))
            (else
              (let ((new (make-node item '() front-ptr)))
                ((front-ptr 'set-previous-ptr!) new)
                (set! front-ptr new))))
      front-ptr)
    (define (rear-insert-deque! item)
      (cond ((empty-deque?)
             (let ((new (make-node item '() '())))
               (set! front-ptr new)
               (set! rear-ptr new)))
            (else
              (let ((new (make-node item rear-ptr '())))
                ((rear-ptr 'set-next-ptr!) new)
                (set! rear-ptr new))))
      front-ptr)

    (define (front-delete-deque!)
      (cond ((empty-deque?)
             (error "FRONT-DELETE-DEQUE! called with an empty deque"))
            ((eq? front-ptr rear-ptr)
             (set! front-ptr '())
             (set! rear-ptr '())
             front-ptr)
            (else
              (let ((tmp front-ptr))
                (set! front-ptr (front-ptr 'next-ptr))
                ((front-ptr 'set-previous-ptr!) '())
                ((tmp 'reset-links!))
                front-ptr))))
    (define (rear-delete-deque!)
      (cond ((empty-deque?)
             (error "REAR-DELETE-DEQUE! called with an empty deque"))
            ((eq? front-ptr rear-ptr)
             (set! front-ptr '())
             (set! rear-ptr '())
             front-ptr)
            (else
              (let ((tmp rear-ptr))
                (set! rear-ptr (rear-ptr 'previous-ptr))
                ((rear-ptr 'set-next-ptr!) '())
                ((tmp 'reset-links!))
                front-ptr))))

    (define (iterate-deque cur next func)
      (if (not (null? cur))
          (begin
            (func cur)
            (iterate-deque (next cur) next func))))
    (define (print-deque)
      (display "(")
      (iterate-deque front-ptr
                     (lambda (node) (node 'next-ptr))
                     (lambda (node)
                       (display (node 'item))
                       (display " ")))
      (display ")"))

    (define (dispatch m)
      (cond ((eq? m 'front-deque) front-deque)
            ((eq? m 'rear-deque) rear-deque)
            ((eq? m 'empty-deque?) empty-deque?)
            ((eq? m 'front-insert-deque!) front-insert-deque!)
            ((eq? m 'rear-insert-deque!) rear-insert-deque!)
            ((eq? m 'front-delete-deque!) front-delete-deque!)
            ((eq? m 'rear-delete-deque!) rear-delete-deque!)
            ((eq? m 'print-deque) print-deque)
            (else (error "Unknown operation -- DISPATCH of deque" m))))
    dispatch))
