import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeClimbingDisplacement extends Action<'changeClimbingDisplacement'> {
    constructor(params: ActionSubClassParams<'changeClimbingDisplacement'>);
    execute(): void;
    getDescription(): string;
}
