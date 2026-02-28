import { Action, type ActionSubClassParams } from './Action';
export declare class AddProficiency extends Action<'addProficiency'> {
    constructor(params: ActionSubClassParams<'addProficiency'>);
    execute(): void;
    getDescription(): string;
}
