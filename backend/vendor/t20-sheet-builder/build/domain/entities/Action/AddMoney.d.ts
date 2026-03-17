import { Action, type ActionSubClassParams } from './Action';
export declare class AddMoney extends Action<'addMoney'> {
    constructor(params: ActionSubClassParams<'addMoney'>);
    execute(): void;
    getDescription(): string;
}
