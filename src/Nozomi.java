
public class Nozomi extends Train{
	int elec;
	@Override
	public void run() {
		System.out.println("バビューン");
	}
	@Override
	public void open() {
		System.out.println("開きます");
	}
	@Override
	public void close() {
		System.out.println("閉まります");
	}
}

