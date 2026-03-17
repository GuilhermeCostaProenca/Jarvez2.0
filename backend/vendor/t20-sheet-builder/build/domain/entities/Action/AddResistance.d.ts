import { Action, type ActionSubClassParams } from './Action';
export declare class AddResistance extends Action<'addResistance'> {
    constructor(params: ActionSubClassParams<'addResistance'>);
    execute(): void;
    getDescription(): string;
}
