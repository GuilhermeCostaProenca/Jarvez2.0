import { Action, type ActionSubClassParams } from './Action';
export declare class PickGeneralPower extends Action<'pickGeneralPower'> {
    constructor(params: ActionSubClassParams<'pickGeneralPower'>);
    execute(): void;
    getDescription(): string;
}
