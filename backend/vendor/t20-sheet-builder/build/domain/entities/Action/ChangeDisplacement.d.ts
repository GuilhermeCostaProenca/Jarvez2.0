import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeDisplacement extends Action<'changeDisplacement'> {
    constructor(params: ActionSubClassParams<'changeDisplacement'>);
    execute(): void;
    getDescription(): string;
}
