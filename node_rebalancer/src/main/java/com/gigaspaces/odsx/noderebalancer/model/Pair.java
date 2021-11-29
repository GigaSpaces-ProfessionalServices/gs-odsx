package com.gigaspaces.odsx.noderebalancer.model;

/**
 *  Holder class for a pair of two values of two arbitrary types.
 * @param <T1> first constituent of type T1
 * @param <T2> second constituent of type T2
 */
public class Pair<T1, T2> {

    T1 first;
    T2 second;

    public Pair(T1 first, T2 second) {
        this.first = first;
        this.second = second;
    }

    public T1 getFirst() {
        return first;
    }

    public T2 getSecond() {
        return second;
    }
}
