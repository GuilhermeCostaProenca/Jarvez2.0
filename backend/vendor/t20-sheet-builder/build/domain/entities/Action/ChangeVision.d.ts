import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeVision extends Action<'changeVision'> {
    constructor(params: ActionSubClassParams<'changeVision'>);
    execute(): void;
    getDescription(): string;
}
