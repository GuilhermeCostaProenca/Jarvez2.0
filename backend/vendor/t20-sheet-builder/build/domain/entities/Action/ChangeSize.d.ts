import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeSize extends Action<'changeSize'> {
    constructor(params: ActionSubClassParams<'changeSize'>);
    execute(): void;
    getDescription(): string;
}
