import { type Action } from './Action/Action';
import type { Queue } from './Queue';
export declare class ActionsQueue implements Queue<Action> {
    items: Action[];
    enqueue(item: Action): void;
    dequeue(): Action;
    getSize(): number;
}
