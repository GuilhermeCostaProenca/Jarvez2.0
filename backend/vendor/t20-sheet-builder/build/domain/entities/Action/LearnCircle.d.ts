import { Action, type ActionSubClassParams } from './Action';
export declare class LearnCircle extends Action<'learnCircle'> {
    constructor(params: ActionSubClassParams<'learnCircle'>);
    execute(): void;
    getDescription(): string;
}
